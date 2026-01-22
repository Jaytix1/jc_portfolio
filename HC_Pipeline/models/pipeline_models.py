# Pipeline models are defined in Histacruise/app.py to use the shared db instance.
# This module re-exports them for convenience.
#
# The following models are added to app.py:
# - StockPrice: Daily stock prices for CCL, RCL, NCLH
# - IndustryNews: News articles from RSS feeds
# - CruiseDeal: Cruise deals and pricing
# - ShipSpecification: Extended ship data
# - PipelineRun: Pipeline execution logs

def get_models_code():
    """Returns the model definitions to be added to app.py."""
    return '''
# ============== PIPELINE MODELS ==============

class StockPrice(db.Model):
    """Daily stock prices for cruise companies (CCL, RCL, NCLH)."""
    __tablename__ = 'stock_price'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    open_price = db.Column(db.Float, nullable=True)
    high_price = db.Column(db.Float, nullable=True)
    low_price = db.Column(db.Float, nullable=True)
    close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('symbol', 'date', name='unique_stock_date'),
    )

    def __repr__(self):
        return f'<StockPrice {self.symbol} {self.date}: ${self.close_price}>'


class IndustryNews(db.Model):
    """Cruise industry news articles from RSS feeds."""
    __tablename__ = 'industry_news'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(1000), nullable=False, unique=True)
    source_name = db.Column(db.String(100), nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(100), nullable=True)
    related_cruiseline_id = db.Column(db.Integer, db.ForeignKey('cruise_line.id'), nullable=True)

    cruiseline = db.relationship('CruiseLine', backref='news_articles')

    def __repr__(self):
        return f'<IndustryNews {self.title[:30]}...>'


class CruiseDeal(db.Model):
    """Tracked cruise deals and pricing."""
    __tablename__ = 'cruise_deal'

    id = db.Column(db.Integer, primary_key=True)
    cruiseline_id = db.Column(db.Integer, db.ForeignKey('cruise_line.id'), nullable=True)
    ship_id = db.Column(db.Integer, db.ForeignKey('ship.id'), nullable=True)
    title = db.Column(db.String(500), nullable=False)
    departure_date = db.Column(db.Date, nullable=True)
    duration_nights = db.Column(db.Integer, nullable=True)
    departure_port = db.Column(db.String(200), nullable=True)
    destination_region = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=True)
    original_price = db.Column(db.Float, nullable=True)
    price_per_night = db.Column(db.Float, nullable=True)
    cabin_type = db.Column(db.String(100), nullable=True)
    source_url = db.Column(db.String(1000), nullable=True)
    source_name = db.Column(db.String(100), nullable=True)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    cruiseline = db.relationship('CruiseLine', backref='deals')
    ship = db.relationship('Ship', backref='deals')

    def __repr__(self):
        return f'<CruiseDeal {self.title[:30]}... ${self.price}>'


class ShipSpecification(db.Model):
    """Detailed ship specifications extending the Ship model."""
    __tablename__ = 'ship_specification'

    id = db.Column(db.Integer, primary_key=True)
    ship_id = db.Column(db.Integer, db.ForeignKey('ship.id'), nullable=False, unique=True)
    gross_tonnage = db.Column(db.Integer, nullable=True)
    length_meters = db.Column(db.Float, nullable=True)
    beam_meters = db.Column(db.Float, nullable=True)
    draft_meters = db.Column(db.Float, nullable=True)
    passenger_capacity = db.Column(db.Integer, nullable=True)
    crew_capacity = db.Column(db.Integer, nullable=True)
    deck_count = db.Column(db.Integer, nullable=True)
    year_built = db.Column(db.Integer, nullable=True)
    year_refurbished = db.Column(db.Integer, nullable=True)
    builder = db.Column(db.String(200), nullable=True)
    ship_class = db.Column(db.String(100), nullable=True)
    registry = db.Column(db.String(100), nullable=True)
    imo_number = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(50), default='active')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    data_source = db.Column(db.String(100), nullable=True)

    ship = db.relationship('Ship', backref=db.backref('specifications', uselist=False))

    def __repr__(self):
        return f'<ShipSpecification ship_id={self.ship_id}>'


class PipelineRun(db.Model):
    """Tracks pipeline execution history."""
    __tablename__ = 'pipeline_run'

    id = db.Column(db.Integer, primary_key=True)
    run_type = db.Column(db.String(50), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False)
    records_processed = db.Column(db.Integer, default=0)
    records_added = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<PipelineRun {self.run_type} {self.status}>'
'''
