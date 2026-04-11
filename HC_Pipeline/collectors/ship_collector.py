import logging
import re
from datetime import datetime
from .base_collector import BaseCollector

try:
    import requests
except ImportError:
    requests = None


class ShipCollector(BaseCollector):
    """Collector for ship specifications from Wikipedia."""

    WIKIPEDIA_API = 'https://en.wikipedia.org/w/api.php'

    # Mapping of known cruise line names to Wikipedia category/search terms
    CRUISELINE_WIKI_TERMS = {
        'Carnival': 'Carnival Cruise Line ships',
        'Royal Caribbean': 'Royal Caribbean International ships',
        'Norwegian': 'Norwegian Cruise Line ships',
        'Princess': 'Princess Cruises ships',
        'Celebrity': 'Celebrity Cruises ships',
        'MSC': 'MSC Cruises ships',
        'Holland America': 'Holland America Line ships',
        'Disney': 'Disney Cruise Line ships',
    }

    def __init__(self, db_session, logger=None):
        super().__init__(db_session, logger)
        if requests is None:
            raise ImportError("requests is required. Install with: pip install requests")

    def collect(self) -> bool:
        """
        Collect ship specifications for existing ships in the database.

        Returns:
            bool: True on success, False on failure
        """
        from Histacruise.app import Ship, ShipSpecification

        self.reset_stats()
        self.logger.info("Starting ship specification collection")

        # Get all ships that don't have specifications yet
        ships = self.db.query(Ship).outerjoin(ShipSpecification).filter(
            ShipSpecification.id == None
        ).all()

        if not ships:
            self.logger.info("All ships already have specifications")
            return True

        self.logger.info(f"Found {len(ships)} ships without specifications")

        for ship in ships:
            self.stats['processed'] += 1
            try:
                specs = self._fetch_ship_specs(ship.name, ship.cruiseline.name if ship.cruiseline else None)
                if specs:
                    self._save_specs(ship.id, specs, ShipSpecification)
                    self.stats['added'] += 1
            except Exception as e:
                self.logger.error(f"Error fetching specs for {ship.name}: {e}")
                self.stats['errors'] += 1

        self.db.commit()
        self.logger.info(
            f"Ship collection complete: {self.stats['processed']} processed, "
            f"{self.stats['added']} added, {self.stats['errors']} errors"
        )
        return True

    def _fetch_ship_specs(self, ship_name: str, cruiseline_name: str = None) -> dict:
        """Fetch ship specifications from Wikipedia."""
        # Build search query
        search_term = f"{ship_name} cruise ship"
        if cruiseline_name:
            search_term = f"{ship_name} {cruiseline_name}"

        # Search for the page
        search_params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': search_term,
            'srlimit': 1
        }

        try:
            response = requests.get(self.WIKIPEDIA_API, params=search_params, timeout=10,
                                    headers={'User-Agent': 'Histacruise/1.0 (cruise tracking app)'})
            if response.status_code == 403:
                self.logger.debug(f"Wikipedia blocked request for {ship_name}, skipping")
                return None
            response.raise_for_status()
            data = response.json()

            search_results = data.get('query', {}).get('search', [])
            if not search_results:
                self.logger.debug(f"No Wikipedia page found for {ship_name}")
                return None

            page_title = search_results[0]['title']

            # Fetch page content
            return self._fetch_page_specs(page_title)

        except requests.RequestException as e:
            self.logger.error(f"Wikipedia API error for {ship_name}: {e}")
            return None

    def _fetch_page_specs(self, page_title: str) -> dict:
        """Fetch specifications from a Wikipedia page."""
        params = {
            'action': 'query',
            'format': 'json',
            'titles': page_title,
            'prop': 'revisions',
            'rvprop': 'content',
            'rvslots': 'main'
        }

        try:
            response = requests.get(self.WIKIPEDIA_API, params=params, timeout=10,
                                    headers={'User-Agent': 'Histacruise/1.0 (cruise tracking app)'})
            if response.status_code == 403:
                return None
            response.raise_for_status()
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return None

            page = list(pages.values())[0]
            if 'revisions' not in page:
                return None

            content = page['revisions'][0]['slots']['main']['*']

            # Parse infobox for ship specifications
            return self._parse_infobox(content)

        except (requests.RequestException, KeyError, IndexError) as e:
            self.logger.error(f"Error fetching page {page_title}: {e}")
            return None

    def _parse_infobox(self, content: str) -> dict:
        """Parse ship specifications from Wikipedia infobox."""
        specs = {}

        # Common infobox patterns for ships
        patterns = {
            'gross_tonnage': r'\|\s*(?:Tonnage|Gross tonnage)\s*=\s*([\d,]+)',
            'length_meters': r'\|\s*Length\s*=\s*([\d.]+)\s*m',
            'beam_meters': r'\|\s*Beam\s*=\s*([\d.]+)\s*m',
            'draft_meters': r'\|\s*Draft\s*=\s*([\d.]+)\s*m',
            'passenger_capacity': r'\|\s*(?:Passengers|Capacity)\s*=\s*([\d,]+)',
            'crew_capacity': r'\|\s*Crew\s*=\s*([\d,]+)',
            'deck_count': r'\|\s*Decks\s*=\s*(\d+)',
            'year_built': r'\|\s*(?:Completed|Built|Launched)\s*=\s*.*?(\d{4})',
            'builder': r'\|\s*Builder\s*=\s*\[\[([^\]|]+)',
            'ship_class': r'\|\s*Class\s*=\s*\[\[([^\]|]+)',
            'imo_number': r'\|\s*IMO number\s*=\s*(\d+)',
            'registry': r'\|\s*(?:Flag|Port of registry)\s*=\s*(?:\{\{flagicon\|)?([A-Za-z ]+)',
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '').strip()

                # Convert to appropriate type
                if field in ['gross_tonnage', 'passenger_capacity', 'crew_capacity', 'deck_count', 'year_built']:
                    try:
                        specs[field] = int(value)
                    except ValueError:
                        pass
                elif field in ['length_meters', 'beam_meters', 'draft_meters']:
                    try:
                        specs[field] = float(value)
                    except ValueError:
                        pass
                else:
                    specs[field] = value[:200]  # Limit string length

        return specs if specs else None

    def _save_specs(self, ship_id: int, specs: dict, ShipSpecification):
        """Save ship specifications to database."""
        spec = ShipSpecification(
            ship_id=ship_id,
            gross_tonnage=specs.get('gross_tonnage'),
            length_meters=specs.get('length_meters'),
            beam_meters=specs.get('beam_meters'),
            draft_meters=specs.get('draft_meters'),
            passenger_capacity=specs.get('passenger_capacity'),
            crew_capacity=specs.get('crew_capacity'),
            deck_count=specs.get('deck_count'),
            year_built=specs.get('year_built'),
            builder=specs.get('builder'),
            ship_class=specs.get('ship_class'),
            imo_number=specs.get('imo_number'),
            registry=specs.get('registry'),
            status='active',
            data_source='wikipedia'
        )
        self.db.add(spec)

    def update_ship_specs(self, ship_id: int) -> bool:
        """Update specifications for a specific ship."""
        from Histacruise.app import Ship, ShipSpecification

        ship = self.db.query(Ship).get(ship_id)
        if not ship:
            return False

        specs = self._fetch_ship_specs(ship.name, ship.cruiseline.name if ship.cruiseline else None)
        if not specs:
            return False

        existing = self.db.query(ShipSpecification).filter_by(ship_id=ship_id).first()
        if existing:
            for key, value in specs.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.last_updated = datetime.utcnow()
        else:
            self._save_specs(ship_id, specs, ShipSpecification)

        self.db.commit()
        return True
