"""
HC_Pipeline - Main Pipeline Orchestrator

Coordinates data collection for cruise industry data:
- Stock prices (CCL, RCL, NCLH)
- Industry news from RSS feeds
- Cruise deals
- Ship specifications
"""

import logging
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from HC_Pipeline.collectors.stock_collector import StockCollector
from HC_Pipeline.collectors.news_collector import NewsCollector
from HC_Pipeline.collectors.deals_collector import DealsCollector
from HC_Pipeline.collectors.ship_collector import ShipCollector


class Pipeline:
    """Main pipeline orchestrator."""

    def __init__(self, app=None):
        """
        Initialize the pipeline.

        Args:
            app: Flask app instance. If None, creates a new app context.
        """
        self.app = app
        self.db = None
        self.logger = self._setup_logging()

        if app is None:
            self._init_app()

    def _setup_logging(self):
        """Configure logging for the pipeline."""
        logger = logging.getLogger('HC_Pipeline')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # Console handler
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console.setFormatter(formatter)
            logger.addHandler(console)

            # File handler (optional)
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(
                os.path.join(log_dir, f'pipeline_{datetime.now().strftime("%Y%m")}.log')
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def _init_app(self):
        """Initialize Flask app and database session."""
        from Histacruise.app import app, db
        self.app = app
        self.db = db.session

    def run_stocks(self) -> bool:
        """Run stock price collection."""
        self.logger.info("=" * 50)
        self.logger.info("Starting stock price collection")

        with self.app.app_context():
            from Histacruise.app import db
            collector = StockCollector(db.session, self.logger)
            run = collector.log_run('stocks', 'running')

            try:
                success = collector.collect()
                collector.complete_run(run, 'success' if success else 'failed')
                return success
            except Exception as e:
                self.logger.error(f"Stock collection failed: {e}")
                collector.complete_run(run, 'failed', str(e))
                return False

    def run_news(self) -> bool:
        """Run news collection from RSS feeds."""
        self.logger.info("=" * 50)
        self.logger.info("Starting news collection")

        with self.app.app_context():
            from Histacruise.app import db
            collector = NewsCollector(db.session, logger=self.logger)
            run = collector.log_run('news', 'running')

            try:
                success = collector.collect()
                collector.complete_run(run, 'success' if success else 'partial')
                return success
            except Exception as e:
                self.logger.error(f"News collection failed: {e}")
                collector.complete_run(run, 'failed', str(e))
                return False

    def run_deals(self) -> bool:
        """Run cruise deals collection."""
        self.logger.info("=" * 50)
        self.logger.info("Starting deals collection")

        with self.app.app_context():
            from Histacruise.app import db
            collector = DealsCollector(db.session, logger=self.logger)
            run = collector.log_run('deals', 'running')

            try:
                success = collector.collect()
                # Also clean up expired deals
                collector.mark_expired_deals()
                collector.complete_run(run, 'success' if success else 'partial')
                return success
            except Exception as e:
                self.logger.error(f"Deals collection failed: {e}")
                collector.complete_run(run, 'failed', str(e))
                return False

    def run_ships(self) -> bool:
        """Run ship specification collection."""
        self.logger.info("=" * 50)
        self.logger.info("Starting ship specification collection")

        with self.app.app_context():
            from Histacruise.app import db
            collector = ShipCollector(db.session, self.logger)
            run = collector.log_run('ships', 'running')

            try:
                success = collector.collect()
                collector.complete_run(run, 'success' if success else 'partial')
                return success
            except Exception as e:
                self.logger.error(f"Ship collection failed: {e}")
                collector.complete_run(run, 'failed', str(e))
                return False

    def run_all(self) -> dict:
        """Run all collectors."""
        self.logger.info("=" * 50)
        self.logger.info("Starting full pipeline run")
        start_time = datetime.now()

        results = {
            'stocks': self.run_stocks(),
            'news': self.run_news(),
            'deals': self.run_deals(),
            'ships': self.run_ships(),
        }

        elapsed = datetime.now() - start_time
        self.logger.info(f"Full pipeline completed in {elapsed.total_seconds():.1f}s")
        self.logger.info(f"Results: {results}")

        return results

    def get_status(self) -> dict:
        """Get pipeline status and recent runs."""
        with self.app.app_context():
            from Histacruise.app import PipelineRun, db

            recent_runs = db.session.query(PipelineRun).order_by(
                PipelineRun.started_at.desc()
            ).limit(10).all()

            return {
                'recent_runs': [{
                    'type': r.run_type,
                    'status': r.status,
                    'started': r.started_at.isoformat(),
                    'completed': r.completed_at.isoformat() if r.completed_at else None,
                    'records_added': r.records_added,
                    'error': r.error_message
                } for r in recent_runs]
            }


def main():
    """Main entry point for the pipeline."""
    pipeline = Pipeline()
    results = pipeline.run_all()
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
