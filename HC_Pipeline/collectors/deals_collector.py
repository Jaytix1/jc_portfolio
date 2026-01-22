import logging
import re
from datetime import datetime
from .base_collector import BaseCollector

try:
    import feedparser
except ImportError:
    feedparser = None


class DealsCollector(BaseCollector):
    """Collector for cruise deals from RSS feeds and deal sites."""

    DEFAULT_FEEDS = [
        {'name': 'CruiseCritic Deals', 'url': 'https://www.cruisecritic.com/deals/rss/'},
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
        Collect cruise deals from RSS feeds.

        Returns:
            bool: True on success, False on failure
        """
        from Histacruise.app import CruiseDeal, CruiseLine

        self.reset_stats()
        self.logger.info(f"Starting deals collection from {len(self.feeds)} feeds")

        # Load cruise lines for matching
        cruiselines = {cl.name.lower(): cl for cl in self.db.query(CruiseLine).all()}

        success = True
        for feed_config in self.feeds:
            try:
                self._process_feed(feed_config, CruiseDeal, cruiselines)
            except Exception as e:
                self.logger.error(f"Error processing deals feed {feed_config['name']}: {e}")
                self.stats['errors'] += 1
                success = False

        self.db.commit()
        self.logger.info(
            f"Deals collection complete: {self.stats['processed']} processed, "
            f"{self.stats['added']} added, {self.stats['errors']} errors"
        )
        return success

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
