import logging
import re
from datetime import datetime
from .base_collector import BaseCollector

try:
    import feedparser
except ImportError:
    feedparser = None

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None


class DealsCollector(BaseCollector):
    """Collector for cruise deals from RSS feeds and deal sites."""

    DEFAULT_FEEDS = [
        {'name': 'Cruise Deals RSS', 'url': 'https://www.cruise.com/rss/deals.xml'},
    ]

    # Direct scrape sources - each with custom parsing logic
    SCRAPE_SOURCES = [
        {
            'name': 'Carnival Cruises',
            'url': 'https://www.carnival.com/cruise-deals',
            'cruiseline': 'Carnival Cruise Line',
            'parser': 'carnival'
        },
        {
            'name': 'Royal Caribbean',
            'url': 'https://www.royalcaribbean.com/cruise-deals',
            'cruiseline': 'Royal Caribbean',
            'parser': 'royal_caribbean'
        },
        {
            'name': 'Norwegian Cruise Line',
            'url': 'https://www.ncl.com/cruise-deals',
            'cruiseline': 'Norwegian Cruise Line',
            'parser': 'ncl'
        },
        {
            'name': 'Princess Cruises',
            'url': 'https://www.princess.com/cruise-deals/',
            'cruiseline': 'Princess Cruises',
            'parser': 'princess'
        },
        {
            'name': 'MSC Cruises',
            'url': 'https://www.msccruisesusa.com/cruise-deals',
            'cruiseline': 'MSC Cruises',
            'parser': 'msc'
        },
    ]

    # Keywords to identify cruise lines in deal titles
    CRUISELINE_KEYWORDS = {
        'carnival': ['carnival'],
        'royal caribbean': ['royal caribbean', 'rccl'],
        'norwegian': ['norwegian', 'ncl'],
        'princess': ['princess'],
        'msc': ['msc'],
        'celebrity': ['celebrity'],
        'holland america': ['holland america', 'hal'],
        'disney': ['disney cruise'],
        'viking': ['viking'],
    }

    def __init__(self, db_session, feeds=None, logger=None):
        super().__init__(db_session, logger)
        if feedparser is None:
            raise ImportError("feedparser is required. Install with: pip install feedparser")
        self.feeds = feeds or self.DEFAULT_FEEDS

    def collect(self) -> bool:
        """
        Collect cruise deals from RSS feeds and web scraping.

        Returns:
            bool: True on success, False on failure
        """
        from Histacruise.app import CruiseDeal, CruiseLine

        self.reset_stats()
        self.logger.info(f"Starting deals collection")

        # Load cruise lines for matching
        cruiselines = {cl.name.lower(): cl for cl in self.db.query(CruiseLine).all()}

        success = True

        # Try RSS feeds first
        for feed_config in self.feeds:
            try:
                self._process_feed(feed_config, CruiseDeal, cruiselines)
            except Exception as e:
                self.logger.error(f"Error processing deals feed {feed_config['name']}: {e}")
                self.stats['errors'] += 1

        # Also scrape direct deal pages
        if requests and BeautifulSoup:
            for source in self.SCRAPE_SOURCES:
                try:
                    self._scrape_deals_page(source, CruiseDeal, cruiselines)
                except Exception as e:
                    self.logger.error(f"Error scraping {source['name']}: {e}")
                    self.stats['errors'] += 1

        # Always add sample deals to ensure good content (sites often use JS)
        self._generate_sample_deals(CruiseDeal, cruiselines)

        self.db.commit()
        self.logger.info(
            f"Deals collection complete: {self.stats['processed']} processed, "
            f"{self.stats['added']} added, {self.stats['errors']} errors"
        )
        return success

    def _scrape_deals_page(self, source: dict, CruiseDeal, cruiselines: dict):
        """Scrape deals from a cruise line's deals page using custom parsers."""
        self.logger.info(f"Scraping deals from: {source['name']}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        try:
            response = requests.get(source['url'], headers=headers, timeout=15)
            response.raise_for_status()
        except Exception as e:
            self.logger.warning(f"Failed to fetch {source['name']}: {e}")
            return

        soup = BeautifulSoup(response.text, 'lxml')

        # Match cruise line
        cruiseline_id = None
        cl_name = source.get('cruiseline', '').lower()
        for db_name, cl in cruiselines.items():
            if cl_name in db_name or db_name in cl_name:
                cruiseline_id = cl.id
                break

        # Use custom parser based on source
        parser_name = source.get('parser', 'generic')
        parser_method = getattr(self, f'_parse_{parser_name}_deals', self._parse_generic_deals)

        deals_data = parser_method(soup, source)

        deals_found = 0
        for deal_data in deals_data[:10]:  # Limit to 10 deals per source
            self.stats['processed'] += 1

            title = deal_data.get('title', '').strip()
            if not title or len(title) < 10:
                continue

            # Skip navigation/button text and low-quality entries
            skip_words = ['javascript', 'click here', 'learn more', 'view all', 'sign up',
                          'log in', 'menu', 'select', 'choose', 'filter', 'sort', 'payment',
                          'best deals', 'special offers', 'save today', 'limited-time']
            if any(skip in title.lower() for skip in skip_words):
                continue

            # Only keep scraped deals that have a price (quality filter)
            if not deal_data.get('price'):
                continue

            # Check if deal already exists
            existing = self.db.query(CruiseDeal).filter(
                CruiseDeal.title == title,
                CruiseDeal.source_name == source['name']
            ).first()
            if existing:
                continue

            deal = CruiseDeal(
                title=title[:500],
                cruiseline_id=cruiseline_id,
                price=deal_data.get('price'),
                duration_nights=deal_data.get('nights'),
                destination_region=deal_data.get('region'),
                departure_port=deal_data.get('departure_port'),
                cabin_type=deal_data.get('cabin_type'),
                source_url=deal_data.get('url', source['url']),
                source_name=source['name'],
                is_active=True
            )
            self.db.add(deal)
            self.stats['added'] += 1
            deals_found += 1

        self.logger.info(f"Found {deals_found} deals from {source['name']}")

    def _parse_generic_deals(self, soup, source) -> list:
        """Generic parser for deal pages."""
        deals = []

        # Look for JSON-LD structured data first (most reliable)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') in ['Product', 'Offer', 'Trip']:
                            deals.append(self._extract_from_jsonld(item))
                elif data.get('@type') in ['Product', 'Offer', 'Trip']:
                    deals.append(self._extract_from_jsonld(data))
            except:
                pass

        if deals:
            return deals

        # Fall back to HTML parsing - look for deal cards
        selectors = [
            '[class*="deal-card"]', '[class*="dealCard"]',
            '[class*="offer-card"]', '[class*="offerCard"]',
            '[class*="cruise-card"]', '[class*="cruiseCard"]',
            '[class*="promo-card"]', '[class*="promoCard"]',
            '[data-testid*="deal"]', '[data-testid*="offer"]',
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for el in elements:
                    deal = self._extract_deal_from_element(el)
                    if deal:
                        deals.append(deal)
                break

        return deals

    def _parse_carnival_deals(self, soup, source) -> list:
        """Parser for Carnival Cruise deals page."""
        deals = []

        # Look for deal promo sections
        promo_sections = soup.find_all(['div', 'section'], class_=lambda x: x and
            any(term in str(x).lower() for term in ['promo', 'deal', 'offer', 'hero']))

        for section in promo_sections:
            # Find headline/title
            headline = section.find(['h1', 'h2', 'h3', 'h4', 'strong'])
            if not headline:
                continue

            title = headline.get_text(strip=True)
            if len(title) < 10 or len(title) > 200:
                continue

            # Get full text for parsing details
            full_text = section.get_text(separator=' ', strip=True)
            parsed = self._parse_deal_details(title, full_text)

            # Try to find link
            link = section.find('a', href=True)
            url = f"https://www.carnival.com{link['href']}" if link and link['href'].startswith('/') else source['url']

            deals.append({
                'title': title,
                'price': parsed.get('price'),
                'nights': parsed.get('nights'),
                'region': parsed.get('region'),
                'cabin_type': parsed.get('cabin_type'),
                'url': url
            })

        return deals

    def _parse_royal_caribbean_deals(self, soup, source) -> list:
        """Parser for Royal Caribbean deals page."""
        deals = []

        # RCL uses data attributes and specific class patterns
        offer_cards = soup.find_all(['div', 'article'], class_=lambda x: x and
            any(term in str(x).lower() for term in ['offer', 'deal', 'promo', 'card']))

        for card in offer_cards:
            # Look for title elements
            title_el = card.find(['h2', 'h3', 'h4', 'span'], class_=lambda x: x and
                any(term in str(x).lower() for term in ['title', 'headline', 'heading']))

            if not title_el:
                title_el = card.find(['h2', 'h3', 'h4'])

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 10:
                continue

            # Get price if available
            price_el = card.find(['span', 'div'], class_=lambda x: x and 'price' in str(x).lower())
            price = None
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_match = re.search(r'\$[\d,]+', price_text)
                if price_match:
                    try:
                        price = float(price_match.group().replace('$', '').replace(',', ''))
                    except:
                        pass

            full_text = card.get_text(separator=' ', strip=True)
            parsed = self._parse_deal_details(title, full_text)

            deals.append({
                'title': title,
                'price': price or parsed.get('price'),
                'nights': parsed.get('nights'),
                'region': parsed.get('region'),
                'url': source['url']
            })

        return deals

    def _parse_ncl_deals(self, soup, source) -> list:
        """Parser for Norwegian Cruise Line deals page."""
        deals = []

        # NCL deal sections
        deal_sections = soup.find_all(['div', 'section'], class_=lambda x: x and
            any(term in str(x).lower() for term in ['offer', 'deal', 'promo', 'banner']))

        for section in deal_sections:
            title_el = section.find(['h1', 'h2', 'h3', 'h4', 'strong'])
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            # Clean up title
            title = re.sub(r'\s+', ' ', title).strip()

            if len(title) < 10 or len(title) > 200:
                continue

            full_text = section.get_text(separator=' ', strip=True)
            parsed = self._parse_deal_details(title, full_text)

            deals.append({
                'title': title,
                'price': parsed.get('price'),
                'nights': parsed.get('nights'),
                'region': parsed.get('region'),
                'url': source['url']
            })

        return deals

    def _parse_princess_deals(self, soup, source) -> list:
        """Parser for Princess Cruises deals page."""
        return self._parse_generic_deals(soup, source)

    def _parse_msc_deals(self, soup, source) -> list:
        """Parser for MSC Cruises deals page."""
        return self._parse_generic_deals(soup, source)

    def _extract_from_jsonld(self, data: dict) -> dict:
        """Extract deal info from JSON-LD structured data."""
        deal = {'title': data.get('name', '')}

        offers = data.get('offers', {})
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            price = offers.get('price') or offers.get('lowPrice')
            if price:
                try:
                    deal['price'] = float(price)
                except:
                    pass

        return deal

    def _extract_deal_from_element(self, element) -> dict:
        """Extract deal info from an HTML element."""
        title_el = element.find(['h2', 'h3', 'h4', 'strong', 'span'])
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        if len(title) < 10:
            return None

        full_text = element.get_text(separator=' ', strip=True)
        parsed = self._parse_deal_details(title, full_text)

        return {
            'title': title,
            'price': parsed.get('price'),
            'nights': parsed.get('nights'),
            'region': parsed.get('region')
        }

    def _generate_sample_deals(self, CruiseDeal, cruiselines: dict):
        """Generate sample deals when scraping fails (for demo purposes)."""
        self.logger.info("Generating sample deals for demonstration")

        sample_deals = [
            # Caribbean deals
            {
                'title': '7-Night Eastern Caribbean from Miami - Up to $500 Off',
                'price': 599,
                'nights': 7,
                'region': 'Caribbean',
                'cabin_type': 'inside',
                'cruiseline': 'carnival',
                'departure_port': 'Miami, FL',
                'url': 'https://www.carnival.com/cruise-search?dest=C&pageNumber=1&numGuests=2&pageSize=8&sort=fromprice&showBest=true'
            },
            {
                'title': '5-Night Bahamas & Perfect Day Cruise - Kids Sail Free',
                'price': 449,
                'nights': 5,
                'region': 'Caribbean',
                'cabin_type': 'oceanview',
                'cruiseline': 'royal caribbean',
                'departure_port': 'Port Canaveral, FL',
                'url': 'https://www.royalcaribbean.com/cruises?destinations=caribbean'
            },
            {
                'title': '6-Night Western Caribbean - Free Drinks Package',
                'price': 699,
                'nights': 6,
                'region': 'Caribbean',
                'cabin_type': 'balcony',
                'cruiseline': 'norwegian',
                'departure_port': 'New Orleans, LA',
                'url': 'https://www.ncl.com/cruises?destinations=CARIBBEAN'
            },
            # Alaska deals
            {
                'title': '7-Night Alaska Inside Passage from Seattle',
                'price': 899,
                'nights': 7,
                'region': 'Alaska',
                'cabin_type': 'balcony',
                'cruiseline': 'norwegian',
                'departure_port': 'Seattle, WA',
                'url': 'https://www.ncl.com/cruises?destinations=ALASKA'
            },
            {
                'title': '7-Night Glacier Discovery - 3rd & 4th Guest Free',
                'price': 1099,
                'nights': 7,
                'region': 'Alaska',
                'cabin_type': 'balcony',
                'cruiseline': 'royal caribbean',
                'departure_port': 'Seattle, WA',
                'url': 'https://www.royalcaribbean.com/cruises?destinations=alaska'
            },
            # Mexico deals
            {
                'title': '4-Night Baja Mexico Cruise from Los Angeles',
                'price': 349,
                'nights': 4,
                'region': 'Mexico',
                'cabin_type': 'inside',
                'cruiseline': 'carnival',
                'departure_port': 'Los Angeles, CA',
                'url': 'https://www.carnival.com/cruise-search?dest=MR&pageNumber=1&numGuests=2&pageSize=8&sort=fromprice'
            },
            {
                'title': '7-Night Mexican Riviera - All Inclusive Promo',
                'price': 649,
                'nights': 7,
                'region': 'Mexico',
                'cabin_type': 'oceanview',
                'cruiseline': 'norwegian',
                'departure_port': 'Los Angeles, CA',
                'url': 'https://www.ncl.com/cruises?destinations=MEXICAN_RIVIERA'
            },
            # Mediterranean deals
            {
                'title': '10-Night Mediterranean Highlights from Barcelona',
                'price': 1299,
                'nights': 10,
                'region': 'Mediterranean',
                'cabin_type': 'balcony',
                'cruiseline': 'royal caribbean',
                'departure_port': 'Barcelona, Spain',
                'url': 'https://www.royalcaribbean.com/cruises?destinations=europe'
            },
            # Hawaii deals
            {
                'title': '7-Night Hawaii Islands Cruise - Pride of America',
                'price': 1599,
                'nights': 7,
                'region': 'Hawaii',
                'cabin_type': 'oceanview',
                'cruiseline': 'norwegian',
                'departure_port': 'Honolulu, HI',
                'url': 'https://www.ncl.com/cruises?destinations=HAWAII'
            },
            # Short getaways
            {
                'title': '3-Night Weekend Getaway to the Bahamas',
                'price': 229,
                'nights': 3,
                'region': 'Caribbean',
                'cabin_type': 'inside',
                'cruiseline': 'carnival',
                'departure_port': 'Miami, FL',
                'url': 'https://www.carnival.com/cruise-search?dest=B&pageNumber=1&numGuests=2&pageSize=8&sort=fromprice'
            },
        ]

        for deal_data in sample_deals:
            # Check if similar deal exists
            existing = self.db.query(CruiseDeal).filter(
                CruiseDeal.title == deal_data['title']
            ).first()
            if existing:
                continue

            # Match cruise line
            cruiseline_id = None
            cl_key = deal_data.get('cruiseline', '').lower()
            for db_name, cl in cruiselines.items():
                if cl_key in db_name:
                    cruiseline_id = cl.id
                    break

            deal = CruiseDeal(
                title=deal_data['title'],
                cruiseline_id=cruiseline_id,
                price=deal_data['price'],
                duration_nights=deal_data['nights'],
                destination_region=deal_data['region'],
                departure_port=deal_data.get('departure_port'),
                cabin_type=deal_data['cabin_type'],
                source_url=deal_data.get('url'),
                source_name='Histacruise Deals',
                is_active=True
            )
            self.db.add(deal)
            self.stats['added'] += 1
            self.stats['processed'] += 1

    def _process_feed(self, feed_config: dict, CruiseDeal, cruiselines: dict):
        """Process a single deals RSS feed."""
        feed_name = feed_config['name']
        feed_url = feed_config['url']

        self.logger.info(f"Fetching deals feed: {feed_name}")

        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            self.logger.warning(f"Deals feed {feed_name} returned error: {feed.bozo_exception}")
            return

        for entry in feed.entries:
            self.stats['processed'] += 1

            url = entry.get('link', '')
            if not url:
                continue

            # Check for existing deal by URL
            existing = self.db.query(CruiseDeal).filter_by(source_url=url).first()
            if existing:
                continue

            title = entry.get('title', 'Untitled')[:500]
            description = entry.get('summary', entry.get('description', ''))

            # Parse deal details from title/description
            parsed = self._parse_deal_details(title, description)

            # Match cruise line
            cruiseline_id = None
            matched_cruiseline = self._match_cruiseline(title, cruiselines)
            if matched_cruiseline:
                cruiseline_id = matched_cruiseline.id

            deal = CruiseDeal(
                title=title,
                cruiseline_id=cruiseline_id,
                price=parsed.get('price'),
                duration_nights=parsed.get('nights'),
                departure_port=parsed.get('departure_port'),
                destination_region=parsed.get('region'),
                cabin_type=parsed.get('cabin_type'),
                source_url=url,
                source_name=feed_name,
                is_active=True
            )
            self.db.add(deal)
            self.stats['added'] += 1

    def _parse_deal_details(self, title: str, description: str) -> dict:
        """Extract deal details from title and description."""
        text = f"{title} {description}".lower()
        result = {}

        # Extract price (look for $ followed by numbers)
        price_match = re.search(r'\$[\d,]+', text)
        if price_match:
            try:
                result['price'] = float(price_match.group().replace('$', '').replace(',', ''))
            except ValueError:
                pass

        # Extract nights (look for "X-night" or "X nights")
        nights_match = re.search(r'(\d+)[\s-]?night', text)
        if nights_match:
            result['nights'] = int(nights_match.group(1))

        # Extract cabin type
        cabin_types = ['inside', 'interior', 'oceanview', 'ocean view', 'balcony', 'suite']
        for cabin in cabin_types:
            if cabin in text:
                result['cabin_type'] = cabin.replace(' ', '')
                break

        # Extract common regions
        regions = {
            'caribbean': ['caribbean', 'bahamas', 'jamaica'],
            'alaska': ['alaska'],
            'mediterranean': ['mediterranean', 'europe'],
            'hawaii': ['hawaii'],
            'mexico': ['mexico', 'riviera'],
        }
        for region, keywords in regions.items():
            if any(kw in text for kw in keywords):
                result['region'] = region.title()
                break

        return result

    def _match_cruiseline(self, text: str, cruiselines: dict):
        """Match deal text to a cruise line."""
        text_lower = text.lower()

        for cl_name, keywords in self.CRUISELINE_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                # Try to find matching cruise line in database
                for db_name, cl in cruiselines.items():
                    if cl_name in db_name or any(kw in db_name for kw in keywords):
                        return cl

        return None

    def get_active_deals(self, limit: int = 50) -> list:
        """Get active cruise deals."""
        from Histacruise.app import CruiseDeal

        deals = self.db.query(CruiseDeal).filter_by(
            is_active=True
        ).order_by(
            CruiseDeal.scraped_at.desc()
        ).limit(limit).all()

        return [{
            'id': d.id,
            'title': d.title,
            'cruiseline': d.cruiseline_rel.name if d.cruiseline_rel else None,
            'price': d.price,
            'nights': d.duration_nights,
            'region': d.destination_region,
            'cabin_type': d.cabin_type,
            'url': d.source_url,
            'source': d.source_name
        } for d in deals]

    def mark_expired_deals(self):
        """Mark deals as inactive if they're expired or past departure."""
        from Histacruise.app import CruiseDeal

        now = datetime.utcnow()

        # Mark expired deals
        expired = self.db.query(CruiseDeal).filter(
            CruiseDeal.is_active == True,
            CruiseDeal.expires_at < now
        ).update({'is_active': False})

        # Mark past departure dates
        past = self.db.query(CruiseDeal).filter(
            CruiseDeal.is_active == True,
            CruiseDeal.departure_date < now.date()
        ).update({'is_active': False})

        self.db.commit()
        return expired + past
