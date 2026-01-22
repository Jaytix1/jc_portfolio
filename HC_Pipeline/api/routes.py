"""
HC_Pipeline API Routes

Flask blueprint providing REST endpoints for pipeline data:
- /api/pipeline/stocks - Stock price data
- /api/pipeline/news - Industry news
- /api/pipeline/deals - Cruise deals
- /api/pipeline/ships - Ship specifications
- /api/pipeline/dashboard - Aggregated dashboard data
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

pipeline_api = Blueprint('pipeline_api', __name__, url_prefix='/api/pipeline')


# ============== STOCK ENDPOINTS ==============

@pipeline_api.route('/stocks', methods=['GET'])
def get_stocks():
    """
    Get stock prices with optional filters.

    Query params:
        symbol: CCL, RCL, or NCLH (optional)
        days: Number of days of history (default 30)
    """
    from Histacruise.app import StockPrice, db

    symbol = request.args.get('symbol')
    days = request.args.get('days', 30, type=int)

    query = db.session.query(StockPrice)
    if symbol:
        query = query.filter_by(symbol=symbol.upper())

    cutoff = datetime.now().date() - timedelta(days=days)
    query = query.filter(StockPrice.date >= cutoff)
    query = query.order_by(StockPrice.date.desc())

    return jsonify([{
        'symbol': s.symbol,
        'date': s.date.isoformat(),
        'open': s.open_price,
        'high': s.high_price,
        'low': s.low_price,
        'close': s.close_price,
        'volume': s.volume
    } for s in query.all()])


@pipeline_api.route('/stocks/latest', methods=['GET'])
def get_latest_stocks():
    """Get the most recent stock prices for all symbols."""
    from Histacruise.app import StockPrice, db

    symbols = ['CCL', 'RCL', 'NCLH']
    results = {}

    for symbol in symbols:
        latest = db.session.query(StockPrice).filter_by(
            symbol=symbol
        ).order_by(StockPrice.date.desc()).first()

        if latest:
            # Get previous day for change calculation
            prev = db.session.query(StockPrice).filter(
                StockPrice.symbol == symbol,
                StockPrice.date < latest.date
            ).order_by(StockPrice.date.desc()).first()

            change = None
            change_pct = None
            if prev and prev.close_price:
                change = round(latest.close_price - prev.close_price, 2)
                change_pct = round((change / prev.close_price) * 100, 2)

            results[symbol] = {
                'date': latest.date.isoformat(),
                'close': latest.close_price,
                'change': change,
                'change_pct': change_pct
            }

    return jsonify(results)


@pipeline_api.route('/stocks/chart/<symbol>', methods=['GET'])
def get_stock_chart(symbol):
    """Get chart data for a specific stock symbol."""
    from Histacruise.app import StockPrice, db

    days = request.args.get('days', 90, type=int)
    cutoff = datetime.now().date() - timedelta(days=days)

    prices = db.session.query(StockPrice).filter(
        StockPrice.symbol == symbol.upper(),
        StockPrice.date >= cutoff
    ).order_by(StockPrice.date.asc()).all()

    return jsonify({
        'labels': [p.date.strftime('%b %d') for p in prices],
        'datasets': [{
            'label': symbol.upper(),
            'data': [p.close_price for p in prices],
            'borderColor': '#667eea',
            'backgroundColor': 'rgba(102, 126, 234, 0.1)',
            'fill': True
        }]
    })


# ============== NEWS ENDPOINTS ==============

@pipeline_api.route('/news', methods=['GET'])
def get_news():
    """
    Get industry news articles.

    Query params:
        source: Filter by source name (optional)
        category: Filter by category (optional)
        days: Number of days back (default 7)
        limit: Number of results (default 20)
    """
    from Histacruise.app import IndustryNews, db

    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 20, type=int)
    source = request.args.get('source')
    category = request.args.get('category')

    cutoff = datetime.utcnow() - timedelta(days=days)
    query = db.session.query(IndustryNews).filter(
        IndustryNews.scraped_at >= cutoff
    )

    if source:
        query = query.filter_by(source_name=source)
    if category:
        query = query.filter_by(category=category)

    query = query.order_by(IndustryNews.published_at.desc().nullslast())
    articles = query.limit(limit).all()

    return jsonify([{
        'id': a.id,
        'title': a.title,
        'summary': a.summary[:300] + '...' if a.summary and len(a.summary) > 300 else a.summary,
        'url': a.url,
        'source': a.source_name,
        'published': a.published_at.isoformat() if a.published_at else None,
        'category': a.category
    } for a in articles])


@pipeline_api.route('/news/sources', methods=['GET'])
def get_news_sources():
    """Get list of available news sources."""
    from Histacruise.app import IndustryNews, db

    sources = db.session.query(IndustryNews.source_name).distinct().all()
    return jsonify([s[0] for s in sources])


# ============== DEALS ENDPOINTS ==============

@pipeline_api.route('/deals', methods=['GET'])
def get_deals():
    """
    Get cruise deals with filtering.

    Query params:
        cruiseline: Filter by cruise line name (optional)
        max_price: Maximum price filter (optional)
        min_nights: Minimum duration (optional)
        limit: Number of results (default 50)
    """
    from Histacruise.app import CruiseDeal, CruiseLine, db

    limit = request.args.get('limit', 50, type=int)
    max_price = request.args.get('max_price', type=float)
    min_nights = request.args.get('min_nights', type=int)
    cruiseline = request.args.get('cruiseline')

    query = db.session.query(CruiseDeal).filter_by(is_active=True)

    if cruiseline:
        query = query.join(CruiseLine).filter(
            CruiseLine.name.ilike(f'%{cruiseline}%')
        )
    if max_price:
        query = query.filter(CruiseDeal.price <= max_price)
    if min_nights:
        query = query.filter(CruiseDeal.duration_nights >= min_nights)

    deals = query.order_by(CruiseDeal.scraped_at.desc()).limit(limit).all()

    return jsonify([{
        'id': d.id,
        'title': d.title,
        'cruiseline': d.cruiseline_rel.name if d.cruiseline_rel else None,
        'ship': d.ship_rel.name if d.ship_rel else None,
        'departure_date': d.departure_date.isoformat() if d.departure_date else None,
        'nights': d.duration_nights,
        'price': d.price,
        'price_per_night': d.price_per_night,
        'cabin_type': d.cabin_type,
        'region': d.destination_region,
        'url': d.source_url,
        'source': d.source_name
    } for d in deals])


@pipeline_api.route('/deals/stats', methods=['GET'])
def get_deal_stats():
    """Get aggregate deal statistics by cruise line."""
    from Histacruise.app import CruiseDeal, CruiseLine, db
    from sqlalchemy import func

    stats = db.session.query(
        CruiseLine.name,
        func.avg(CruiseDeal.price).label('avg_price'),
        func.min(CruiseDeal.price).label('min_price'),
        func.count(CruiseDeal.id).label('deal_count')
    ).join(CruiseLine).filter(
        CruiseDeal.is_active == True
    ).group_by(CruiseLine.name).all()

    return jsonify([{
        'cruiseline': s.name,
        'avg_price': round(s.avg_price, 2) if s.avg_price else None,
        'min_price': s.min_price,
        'deal_count': s.deal_count
    } for s in stats])


# ============== SHIP ENDPOINTS ==============

@pipeline_api.route('/ships', methods=['GET'])
def get_ships():
    """Get ships with their specifications."""
    from Histacruise.app import Ship, ShipSpecification, db

    ships = db.session.query(Ship).all()

    return jsonify([{
        'id': s.id,
        'name': s.name,
        'cruiseline': s.cruiseline.name if s.cruiseline else None,
        'has_specs': s.specifications is not None,
        'specs': {
            'gross_tonnage': s.specifications.gross_tonnage,
            'passenger_capacity': s.specifications.passenger_capacity,
            'year_built': s.specifications.year_built,
            'deck_count': s.specifications.deck_count
        } if s.specifications else None
    } for s in ships])


@pipeline_api.route('/ships/<int:ship_id>', methods=['GET'])
def get_ship_details(ship_id):
    """Get detailed specifications for a specific ship."""
    from Histacruise.app import Ship, db

    ship = db.session.query(Ship).get(ship_id)
    if not ship:
        return jsonify({'error': 'Ship not found'}), 404

    specs = ship.specifications
    return jsonify({
        'id': ship.id,
        'name': ship.name,
        'cruiseline': ship.cruiseline.name if ship.cruiseline else None,
        'specifications': {
            'gross_tonnage': specs.gross_tonnage if specs else None,
            'length_meters': specs.length_meters if specs else None,
            'beam_meters': specs.beam_meters if specs else None,
            'draft_meters': specs.draft_meters if specs else None,
            'passenger_capacity': specs.passenger_capacity if specs else None,
            'crew_capacity': specs.crew_capacity if specs else None,
            'deck_count': specs.deck_count if specs else None,
            'year_built': specs.year_built if specs else None,
            'year_refurbished': specs.year_refurbished if specs else None,
            'builder': specs.builder if specs else None,
            'ship_class': specs.ship_class if specs else None,
            'registry': specs.registry if specs else None,
            'imo_number': specs.imo_number if specs else None,
            'status': specs.status if specs else None,
            'last_updated': specs.last_updated.isoformat() if specs and specs.last_updated else None
        }
    })


# ============== PIPELINE STATUS ==============

@pipeline_api.route('/status', methods=['GET'])
def get_pipeline_status():
    """Get recent pipeline run status."""
    from Histacruise.app import PipelineRun, db

    runs = db.session.query(PipelineRun).order_by(
        PipelineRun.started_at.desc()
    ).limit(10).all()

    return jsonify([{
        'id': r.id,
        'type': r.run_type,
        'started': r.started_at.isoformat(),
        'completed': r.completed_at.isoformat() if r.completed_at else None,
        'status': r.status,
        'records_processed': r.records_processed,
        'records_added': r.records_added,
        'error': r.error_message
    } for r in runs])


# ============== DASHBOARD ENDPOINT ==============

@pipeline_api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get aggregated dashboard data in one call."""
    from Histacruise.app import StockPrice, IndustryNews, CruiseDeal, PipelineRun, db

    # Latest stocks
    stocks = {}
    for symbol in ['CCL', 'RCL', 'NCLH']:
        price = db.session.query(StockPrice).filter_by(
            symbol=symbol
        ).order_by(StockPrice.date.desc()).first()
        if price:
            stocks[symbol] = {
                'close': price.close_price,
                'date': price.date.isoformat()
            }

    # Recent news count
    today = datetime.utcnow().date()
    news_count = db.session.query(IndustryNews).filter(
        IndustryNews.scraped_at >= datetime.combine(today, datetime.min.time())
    ).count()

    # Active deals count
    deals_count = db.session.query(CruiseDeal).filter_by(is_active=True).count()

    # Last pipeline run status
    last_runs = {}
    for run_type in ['stocks', 'news', 'deals', 'ships']:
        run = db.session.query(PipelineRun).filter_by(
            run_type=run_type
        ).order_by(PipelineRun.started_at.desc()).first()
        if run:
            last_runs[run_type] = {
                'status': run.status,
                'last_run': run.started_at.isoformat()
            }

    return jsonify({
        'stocks': stocks,
        'news_today': news_count,
        'active_deals': deals_count,
        'pipeline_status': last_runs,
        'last_updated': datetime.utcnow().isoformat()
    })
