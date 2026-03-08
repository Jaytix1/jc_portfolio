import logging
from datetime import datetime, timedelta
from .base_collector import BaseCollector

try:
    import yfinance as yf
except ImportError:
    yf = None


class StockCollector(BaseCollector):
    """Collector for cruise company stock prices using Yahoo Finance."""

    SYMBOLS = ['CCL', 'RCL', 'NCLH']
    SYMBOL_NAMES = {
        'CCL': 'Carnival Corporation',
        'RCL': 'Royal Caribbean Group',
        'NCLH': 'Norwegian Cruise Line Holdings'
    }

    def __init__(self, db_session, logger=None):
        super().__init__(db_session, logger)
        if yf is None:
            raise ImportError("yfinance is required. Install with: pip install yfinance")

    def collect(self, days: int = 7) -> bool:
        """
        Collect stock prices for cruise companies.
        Downloads each symbol individually to avoid batch format issues.

        Args:
            days: Number of days of history to fetch (default 7 to cover weekends)

        Returns:
            bool: True if at least one symbol succeeded
        """
        from Histacruise.app import StockPrice

        self.reset_stats()
        self.logger.info(f"Starting stock collection for {self.SYMBOLS}")

        any_success = False
        for symbol in self.SYMBOLS:
            try:
                data = yf.download(
                    symbol,
                    period=f'{days}d',
                    interval='1d',
                    progress=False,
                    auto_adjust=True,
                )
                if data.empty:
                    self.logger.warning(f"No data returned for {symbol}")
                    continue
                self._process_symbol(symbol, data, StockPrice)
                any_success = True
            except Exception as e:
                self.logger.error(f"Failed to download {symbol}: {e}")
                self.stats['errors'] += 1

        if any_success:
            self.db.commit()
        self.logger.info(
            f"Stock collection complete: {self.stats['processed']} processed, "
            f"{self.stats['added']} added, {self.stats['updated']} updated"
        )
        return any_success

    def _process_symbol(self, symbol: str, data, StockPrice):
        """Process stock data for a single symbol."""
        try:
            for date_idx in data.index:
                self.stats['processed'] += 1
                date = date_idx.date()

                existing = self.db.query(StockPrice).filter_by(
                    symbol=symbol,
                    date=date
                ).first()

                row = data.loc[date_idx]

                # Skip if all values are NaN
                if row.isna().all():
                    continue

                if existing:
                    # Update if close price changed
                    if existing.close_price != row['Close']:
                        existing.open_price = float(row['Open']) if not row.isna()['Open'] else None
                        existing.high_price = float(row['High']) if not row.isna()['High'] else None
                        existing.low_price = float(row['Low']) if not row.isna()['Low'] else None
                        existing.close_price = float(row['Close'])
                        existing.volume = int(row['Volume']) if not row.isna()['Volume'] else None
                        self.stats['updated'] += 1
                else:
                    # Add new record
                    stock_price = StockPrice(
                        symbol=symbol,
                        date=date,
                        open_price=float(row['Open']) if not row.isna()['Open'] else None,
                        high_price=float(row['High']) if not row.isna()['High'] else None,
                        low_price=float(row['Low']) if not row.isna()['Low'] else None,
                        close_price=float(row['Close']),
                        volume=int(row['Volume']) if not row.isna()['Volume'] else None
                    )
                    self.db.add(stock_price)
                    self.stats['added'] += 1

        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {e}")
            self.stats['errors'] += 1

    def get_latest_prices(self) -> dict:
        """Get the most recent prices for all tracked symbols."""
        from Histacruise.app import StockPrice

        results = {}
        for symbol in self.SYMBOLS:
            latest = self.db.query(StockPrice).filter_by(
                symbol=symbol
            ).order_by(StockPrice.date.desc()).first()

            if latest:
                # Get previous day for change calculation
                prev = self.db.query(StockPrice).filter(
                    StockPrice.symbol == symbol,
                    StockPrice.date < latest.date
                ).order_by(StockPrice.date.desc()).first()

                change = None
                change_pct = None
                if prev and prev.close_price:
                    change = latest.close_price - prev.close_price
                    change_pct = (change / prev.close_price) * 100

                results[symbol] = {
                    'name': self.SYMBOL_NAMES.get(symbol, symbol),
                    'date': latest.date.isoformat(),
                    'close': latest.close_price,
                    'change': round(change, 2) if change else None,
                    'change_pct': round(change_pct, 2) if change_pct else None
                }

        return results
