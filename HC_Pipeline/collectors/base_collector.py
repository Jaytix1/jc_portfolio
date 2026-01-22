from abc import ABC, abstractmethod
from datetime import datetime
import logging
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, db_session, logger=None):
        self.db = db_session
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.stats = {
            'processed': 0,
            'added': 0,
            'updated': 0,
            'errors': 0
        }

    @abstractmethod
    def collect(self) -> bool:
        """
        Main collection method.

        Returns:
            bool: True on success, False on failure
        """
        pass

    def reset_stats(self):
        """Reset collection statistics."""
        self.stats = {
            'processed': 0,
            'added': 0,
            'updated': 0,
            'errors': 0
        }

    def log_run(self, run_type: str, status: str, error: str = None):
        """
        Log pipeline run to database.

        Args:
            run_type: Type of collection (stocks, news, deals, ships)
            status: Run status (running, success, failed, partial)
            error: Error message if failed
        """
        from Histacruise.app import PipelineRun

        run = PipelineRun(
            run_type=run_type,
            started_at=datetime.utcnow(),
            status=status,
            records_processed=self.stats['processed'],
            records_added=self.stats['added'],
            records_updated=self.stats['updated'],
            error_message=error
        )
        self.db.add(run)
        self.db.commit()
        return run

    def complete_run(self, run, status: str, error: str = None):
        """Mark a pipeline run as complete."""
        run.completed_at = datetime.utcnow()
        run.status = status
        run.records_processed = self.stats['processed']
        run.records_added = self.stats['added']
        run.records_updated = self.stats['updated']
        if error:
            run.error_message = error
        self.db.commit()
