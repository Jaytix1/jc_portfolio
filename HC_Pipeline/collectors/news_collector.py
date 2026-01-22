import logging
from datetime import datetime
from .base_collector import BaseCollector

try:
    import feedparser
except ImportError:
    feedparser = None


class NewsCollector(BaseCollector):
    """Collector for cruise industry news from RSS feeds."""

    DEFAULT_FEEDS = [
        {'name': 'CruiseHive', 'url': 'https://www.cruisehive.com/feed'},
        {'name': 'CruiseCritic', 'url': 'https://www.cruisecritic.com/news/rss/'},
        {'name': 'Maritime Executive', 'url': 'https://maritime-executive.com/rss'},
    ]

    def __init__(self, db_session, feeds=None, logger=None):
        super().__init__(db_session, logger)
        if feedparser is None:
            raise ImportError("feedparser is required. Install with: pip install feedparser")
        self.feeds = feeds or self.DEFAULT_FEEDS

    def collect(self) -> bool:
        """
        Collect news articles from RSS feeds.

        Returns:
            bool: True on success, False on failure
        """
        from Histacruise.app import IndustryNews

        self.reset_stats()
        self.logger.info(f"Starting news collection from {len(self.feeds)} feeds")

        success = True
        for feed_config in self.feeds:
            try:
                self._process_feed(feed_config, IndustryNews)
            except Exception as e:
                self.logger.error(f"Error processing feed {feed_config['name']}: {e}")
                self.stats['errors'] += 1
                success = False

        self.db.commit()
        self.logger.info(
            f"News collection complete: {self.stats['processed']} processed, "
            f"{self.stats['added']} added, {self.stats['errors']} errors"
        )
        return success

    def _process_feed(self, feed_config: dict, IndustryNews):
        """Process a single RSS feed."""
        feed_name = feed_config['name']
        feed_url = feed_config['url']

        self.logger.info(f"Fetching feed: {feed_name}")

        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            self.logger.warning(f"Feed {feed_name} returned error: {feed.bozo_exception}")
            return

        for entry in feed.entries:
            self.stats['processed'] += 1

            # Extract URL (required for deduplication)
            url = entry.get('link', '')
            if not url:
                continue

            # Check if article already exists
            existing = self.db.query(IndustryNews).filter_by(url=url).first()
            if existing:
                continue

            # Parse publication date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except (ValueError, TypeError):
                    pass

            # Extract title and summary
            title = entry.get('title', 'Untitled')[:500]
            summary = entry.get('summary', entry.get('description', ''))

            # Clean HTML from summary
            if summary:
                summary = self._strip_html(summary)[:2000]

            # Detect category from title/summary
            category = self._categorize_article(title, summary)

            # Create news article
            article = IndustryNews(
                title=title,
                summary=summary,
                url=url,
                source_name=feed_name,
                published_at=published_at,
                category=category
            )
            self.db.add(article)
            self.stats['added'] += 1

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def _categorize_article(self, title: str, summary: str) -> str:
        """Categorize article based on keywords."""
        text = f"{title} {summary}".lower()

        categories = {
            'new-ships': ['new ship', 'launch', 'maiden voyage', 'christening', 'debut'],
            'deals': ['deal', 'discount', 'sale', 'offer', 'savings', 'price'],
            'safety': ['safety', 'emergency', 'covid', 'health', 'outbreak', 'incident'],
            'itineraries': ['itinerary', 'route', 'destination', 'port', 'sailing'],
            'company-news': ['earnings', 'stock', 'ceo', 'acquisition', 'financial'],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return 'general'

    def get_recent_news(self, limit: int = 20, days: int = 7) -> list:
        """Get recent news articles."""
        from Histacruise.app import IndustryNews
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)

        articles = self.db.query(IndustryNews).filter(
            IndustryNews.scraped_at >= cutoff
        ).order_by(
            IndustryNews.published_at.desc()
        ).limit(limit).all()

        return [{
            'id': a.id,
            'title': a.title,
            'summary': a.summary[:200] + '...' if a.summary and len(a.summary) > 200 else a.summary,
            'url': a.url,
            'source': a.source_name,
            'published': a.published_at.isoformat() if a.published_at else None,
            'category': a.category
        } for a in articles]
