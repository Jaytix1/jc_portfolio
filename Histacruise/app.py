from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)

# Use absolute path for database to ensure consistency
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "histacruise.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Photo upload configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'cruise_photos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    cruises = db.relationship('CruiseHistory', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    dark_mode = db.Column(db.Boolean, default=False)
    yearly_budget = db.Column(db.Float, nullable=True)
    default_view = db.Column(db.String(20), default='table')

    user = db.relationship('User', backref=db.backref('preferences', uselist=False))

class CruiseLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    ships = db.relationship('Ship', backref='cruiseline', lazy=True)
    
    def __repr__(self):
        return f'<CruiseLine {self.name}>'

class Ship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cruiseline_id = db.Column(db.Integer, db.ForeignKey('cruise_line.id'), nullable=False)
    
    def __repr__(self):
        return f'<Ship {self.name}>'

class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Region {self.name}>'

class CruiseHistory(db.Model):
    cruiseid = db.Column(db.Integer, primary_key=True)
    begindate = db.Column(db.Date, nullable=False)
    enddate = db.Column(db.Date, nullable=False)
    cruiseline_id = db.Column(db.Integer, db.ForeignKey('cruise_line.id'), nullable=False)
    ship_id = db.Column(db.Integer, db.ForeignKey('ship.id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # New optional fields
    cabin_number = db.Column(db.String(20), nullable=True)
    deck = db.Column(db.String(50), nullable=True)
    cost = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    
    # Relationships
    cruiseline = db.relationship('CruiseLine', backref='cruises')
    ship = db.relationship('Ship', backref='cruises')
    region = db.relationship('Region', backref='cruises')

    def __repr__(self):
        return f'<CruiseHistory {self.cruiseid} - {self.ship.name}>'

class CruisePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cruise_id = db.Column(db.Integer, db.ForeignKey('cruise_history.cruiseid'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_cover = db.Column(db.Boolean, default=False)
    caption = db.Column(db.String(500), nullable=True)

    cruise = db.relationship('CruiseHistory', backref='photos')

    def __repr__(self):
        return f'<CruisePhoto {self.id} - {self.original_filename}>'

class Port(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Port {self.name}, {self.country}>'

class CruisePort(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cruise_id = db.Column(db.Integer, db.ForeignKey('cruise_history.cruiseid'), nullable=False)
    port_id = db.Column(db.Integer, db.ForeignKey('port.id'), nullable=False)
    visit_order = db.Column(db.Integer, nullable=False)
    visit_date = db.Column(db.Date, nullable=True)

    cruise = db.relationship('CruiseHistory', backref='cruise_ports')
    port = db.relationship('Port', backref='cruise_ports')

    def __repr__(self):
        return f'<CruisePort {self.cruise_id} - {self.port.name}>'

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

    cruiseline_rel = db.relationship('CruiseLine', backref='deals')
    ship_rel = db.relationship('Ship', backref='deals')

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# Register Pipeline API blueprint
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from HC_Pipeline.api.routes import pipeline_api
app.register_blueprint(pipeline_api)

@app.route('/')
def home():
    # Fetch pipeline data for homepage
    from datetime import timedelta

    # Get latest stock prices
    stocks_data = {}
    for symbol in ['CCL', 'RCL', 'NCLH']:
        latest = db.session.query(StockPrice).filter_by(
            symbol=symbol
        ).order_by(StockPrice.date.desc()).first()

        if latest:
            prev = db.session.query(StockPrice).filter(
                StockPrice.symbol == symbol,
                StockPrice.date < latest.date
            ).order_by(StockPrice.date.desc()).first()

            change = None
            change_pct = None
            if prev and prev.close_price:
                change = round(latest.close_price - prev.close_price, 2)
                change_pct = round((change / prev.close_price) * 100, 2)

            stocks_data[symbol] = {
                'price': latest.close_price,
                'change': change,
                'change_pct': change_pct,
                'date': latest.date
            }

    # Get stock chart data (last 30 days)
    chart_data = {'labels': [], 'ccl': [], 'rcl': [], 'nclh': []}
    ccl_prices = db.session.query(StockPrice).filter(
        StockPrice.symbol == 'CCL'
    ).order_by(StockPrice.date.asc()).limit(30).all()

    for p in ccl_prices:
        chart_data['labels'].append(p.date.strftime('%b %d'))
        chart_data['ccl'].append(p.close_price)

    for symbol in ['RCL', 'NCLH']:
        prices = db.session.query(StockPrice).filter(
            StockPrice.symbol == symbol
        ).order_by(StockPrice.date.asc()).limit(30).all()
        chart_data[symbol.lower()] = [p.close_price for p in prices]

    # Get recent news
    news = db.session.query(IndustryNews).order_by(
        IndustryNews.published_at.desc().nullslast()
    ).limit(5).all()

    # Get active deals
    deals = db.session.query(CruiseDeal).filter_by(
        is_active=True
    ).order_by(CruiseDeal.scraped_at.desc()).limit(4).all()

    return render_template('home.html',
                          stocks=stocks_data,
                          chart_data=chart_data,
                          news=news,
                          deals=deals)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add_cruise', methods=['POST'])
@login_required
def add_cruise():
    begindate = request.form['begindate']
    enddate = request.form['enddate']
    cruiseline_id = request.form['cruiseline_id']
    ship_id = request.form['ship_id']
    region_id = request.form['region_id']

    # Optional fields
    cabin_number = request.form.get('cabin_number', '')
    deck = request.form.get('deck', '')
    cost = request.form.get('cost', None)
    notes = request.form.get('notes', '')
    rating = request.form.get('rating', None)

    begindate_obj = datetime.strptime(begindate, '%Y-%m-%d').date()
    enddate_obj = datetime.strptime(enddate, '%Y-%m-%d').date()

    new_cruise = CruiseHistory(
        begindate=begindate_obj,
        enddate=enddate_obj,
        cruiseline_id=cruiseline_id,
        ship_id=ship_id,
        region_id=region_id,
        cabin_number=cabin_number if cabin_number else None,
        deck=deck if deck else None,
        cost=float(cost) if cost else None,
        notes=notes if notes else None,
        rating=int(rating) if rating else None,
        user_id=current_user.id
    )

    db.session.add(new_cruise)
    db.session.flush()  # Get the cruise ID before committing

    # Handle ports
    port_ids = request.form.getlist('port_ids[]')
    for order, port_id in enumerate(port_ids, 1):
        if port_id:
            cruise_port = CruisePort(
                cruise_id=new_cruise.cruiseid,
                port_id=int(port_id),
                visit_order=order
            )
            db.session.add(cruise_port)

    db.session.commit()

    flash('Cruise added successfully!')
    return redirect(url_for('history'))

@app.route('/delete_cruise/<int:cruise_id>', methods=['POST'])
@login_required
def delete_cruise(cruise_id):
    cruise = CruiseHistory.query.get_or_404(cruise_id)
    
    # Make sure the cruise belongs to the current user
    if cruise.user_id != current_user.id:
        flash('You do not have permission to delete this cruise.')
        return redirect(url_for('history'))
    
    db.session.delete(cruise)
    db.session.commit()
    
    flash('Cruise deleted successfully!')
    return redirect(url_for('history'))

@app.route('/edit_cruise/<int:cruise_id>', methods=['POST'])
@login_required
def edit_cruise(cruise_id):
    cruise = CruiseHistory.query.get_or_404(cruise_id)

    if cruise.user_id != current_user.id:
        flash('You do not have permission to edit this cruise.')
        return redirect(url_for('history'))

    begindate = request.form['begindate']
    enddate = request.form['enddate']
    cruiseline_id = request.form['cruiseline_id']
    ship_id = request.form['ship_id']
    region_id = request.form['region_id']

    # Optional fields
    cabin_number = request.form.get('cabin_number', '')
    deck = request.form.get('deck', '')
    cost = request.form.get('cost', None)
    notes = request.form.get('notes', '')
    rating = request.form.get('rating', None)

    cruise.begindate = datetime.strptime(begindate, '%Y-%m-%d').date()
    cruise.enddate = datetime.strptime(enddate, '%Y-%m-%d').date()
    cruise.cruiseline_id = cruiseline_id
    cruise.ship_id = ship_id
    cruise.region_id = region_id
    cruise.cabin_number = cabin_number if cabin_number else None
    cruise.deck = deck if deck else None
    cruise.cost = float(cost) if cost else None
    cruise.notes = notes if notes else None
    cruise.rating = int(rating) if rating else None

    # Handle ports - remove old ones and add new
    CruisePort.query.filter_by(cruise_id=cruise_id).delete()
    port_ids = request.form.getlist('port_ids[]')
    for order, port_id in enumerate(port_ids, 1):
        if port_id:
            cruise_port = CruisePort(
                cruise_id=cruise_id,
                port_id=int(port_id),
                visit_order=order
            )
            db.session.add(cruise_port)

    db.session.commit()

    flash('Cruise updated successfully!')
    return redirect(url_for('history'))

@app.route('/history')
@login_required
def history():
    cruises = CruiseHistory.query.filter_by(user_id=current_user.id).all()
    cruiselines = CruiseLine.query.order_by(CruiseLine.name).all()
    ships = Ship.query.order_by(Ship.name).all()
    regions = Region.query.order_by(Region.name).all()
    ports = Port.query.order_by(Port.country, Port.name).all()

    return render_template('history.html', cruises=cruises, cruiselines=cruiselines, ships=ships, regions=regions, ports=ports)

@app.route('/statistics')
@login_required
def statistics():
    cruises = CruiseHistory.query.filter_by(user_id=current_user.id).all()

    # Initialize counters
    cruiseline_counts = {}
    region_counts = {}
    ship_counts = {}
    total_days = 0
    total_cost = 0
    cruises_with_cost = 0
    cruises_by_year = {}
    cost_by_year = {}
    cost_by_cruiseline = {}

    for cruise in cruises:
        # Cruise line counts
        line_name = cruise.cruiseline.name
        cruiseline_counts[line_name] = cruiseline_counts.get(line_name, 0) + 1

        # Region counts
        region_name = cruise.region.name
        region_counts[region_name] = region_counts.get(region_name, 0) + 1

        # Ship counts
        ship_name = cruise.ship.name
        ship_counts[ship_name] = ship_counts.get(ship_name, 0) + 1

        # Days calculation
        delta = cruise.enddate - cruise.begindate
        cruise_days = delta.days
        total_days += cruise_days

        # Cost calculations
        if cruise.cost:
            total_cost += cruise.cost
            cruises_with_cost += 1
            if line_name not in cost_by_cruiseline:
                cost_by_cruiseline[line_name] = {'total': 0, 'count': 0}
            cost_by_cruiseline[line_name]['total'] += cruise.cost
            cost_by_cruiseline[line_name]['count'] += 1

        # Year-based aggregation
        year = cruise.begindate.year
        cruises_by_year[year] = cruises_by_year.get(year, 0) + 1
        if cruise.cost:
            cost_by_year[year] = cost_by_year.get(year, 0) + cruise.cost

    # Derived statistics
    avg_cruise_length = total_days / len(cruises) if cruises else 0
    avg_cost = total_cost / cruises_with_cost if cruises_with_cost else 0
    avg_cost_per_day = total_cost / total_days if total_days and total_cost else 0

    # Favorites
    most_sailed_ship = max(ship_counts, key=ship_counts.get) if ship_counts else None
    favorite_cruiseline = max(cruiseline_counts, key=cruiseline_counts.get) if cruiseline_counts else None
    most_visited_region = max(region_counts, key=region_counts.get) if region_counts else None

    # Sort year data for charts
    sorted_years = sorted(cruises_by_year.keys()) if cruises_by_year else []
    cruises_over_time = [cruises_by_year[y] for y in sorted_years]
    costs_over_time = [cost_by_year.get(y, 0) for y in sorted_years]

    # Average cost by cruise line
    avg_cost_by_cruiseline = {
        line: round(data['total'] / data['count'], 2)
        for line, data in cost_by_cruiseline.items()
    }

    # Most/least expensive cruises
    cruises_with_cost_list = sorted(
        [c for c in cruises if c.cost],
        key=lambda x: x.cost,
        reverse=True
    )
    most_expensive = cruises_with_cost_list[0] if cruises_with_cost_list else None
    least_expensive = cruises_with_cost_list[-1] if cruises_with_cost_list else None

    # Budget tracking
    current_year = datetime.now().year
    current_year_spending = sum(
        c.cost for c in cruises
        if c.cost and c.begindate.year == current_year
    )
    user_pref = UserPreference.query.filter_by(user_id=current_user.id).first()
    yearly_budget = user_pref.yearly_budget if user_pref else None
    budget_remaining = (yearly_budget - current_year_spending) if yearly_budget else None

    return render_template('statistics.html',
        cruiseline_counts=cruiseline_counts,
        region_counts=region_counts,
        ship_counts=ship_counts,
        total_days=total_days,
        total_cruises=len(cruises),
        total_cost=total_cost,
        avg_cruise_length=round(avg_cruise_length, 1),
        avg_cost=round(avg_cost, 2),
        avg_cost_per_day=round(avg_cost_per_day, 2),
        most_sailed_ship=most_sailed_ship,
        favorite_cruiseline=favorite_cruiseline,
        most_visited_region=most_visited_region,
        years=sorted_years,
        cruises_over_time=cruises_over_time,
        costs_over_time=costs_over_time,
        avg_cost_by_cruiseline=avg_cost_by_cruiseline,
        most_expensive=most_expensive,
        least_expensive=least_expensive,
        current_year=current_year,
        current_year_spending=current_year_spending,
        yearly_budget=yearly_budget,
        budget_remaining=budget_remaining
    )

@app.route('/set_budget', methods=['POST'])
@login_required
def set_budget():
    budget = request.form.get('yearly_budget', type=float)
    pref = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.session.add(pref)
    pref.yearly_budget = budget
    db.session.commit()
    flash('Budget updated successfully!')
    return redirect(url_for('statistics'))

@app.route('/toggle_dark_mode', methods=['POST'])
@login_required
def toggle_dark_mode():
    pref = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not pref:
        pref = UserPreference(user_id=current_user.id, dark_mode=True)
        db.session.add(pref)
    else:
        pref.dark_mode = not pref.dark_mode
    db.session.commit()
    return jsonify({'dark_mode': pref.dark_mode})

@app.route('/timeline')
@login_required
def timeline():
    cruises = CruiseHistory.query.filter_by(user_id=current_user.id)\
        .order_by(CruiseHistory.begindate.asc()).all()

    timeline_data = []
    for cruise in cruises:
        duration = (cruise.enddate - cruise.begindate).days
        cover_photo = None
        if cruise.photos:
            cover = next((p for p in cruise.photos if p.is_cover), None)
            if cover:
                cover_photo = cover.filename
            elif cruise.photos:
                cover_photo = cruise.photos[0].filename

        timeline_data.append({
            'id': cruise.cruiseid,
            'ship': cruise.ship.name,
            'cruiseline': cruise.cruiseline.name,
            'region': cruise.region.name,
            'begindate': cruise.begindate.isoformat(),
            'enddate': cruise.enddate.isoformat(),
            'begin_display': cruise.begindate.strftime('%b %d, %Y'),
            'end_display': cruise.enddate.strftime('%b %d, %Y'),
            'duration': duration,
            'rating': cruise.rating,
            'cost': cruise.cost,
            'cover_photo': cover_photo
        })

    return render_template('timeline.html', cruises=cruises, timeline_data=timeline_data)

@app.route('/map')
@login_required
def cruise_map():
    cruises = CruiseHistory.query.filter_by(user_id=current_user.id).all()

    map_data = []
    port_visit_counts = {}

    for cruise in cruises:
        cruise_ports_list = CruisePort.query.filter_by(cruise_id=cruise.cruiseid)\
            .order_by(CruisePort.visit_order).all()

        ports_data = []
        for cp in cruise_ports_list:
            port = cp.port
            ports_data.append({
                'name': port.name,
                'country': port.country,
                'lat': port.latitude,
                'lng': port.longitude
            })
            port_visit_counts[port.name] = port_visit_counts.get(port.name, 0) + 1

        map_data.append({
            'id': cruise.cruiseid,
            'ship': cruise.ship.name,
            'cruiseline': cruise.cruiseline.name,
            'year': cruise.begindate.year,
            'region': cruise.region.name,
            'ports': ports_data
        })

    # Generate colors for cruise lines
    cruiselines = list(set(c['cruiseline'] for c in map_data))
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#00c9ff', '#92fe9d']
    cruiseline_colors = {line: colors[i % len(colors)] for i, line in enumerate(cruiselines)}

    # Most visited ports
    most_visited = sorted(port_visit_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return render_template('map.html',
        map_data=map_data,
        cruiseline_colors=cruiseline_colors,
        most_visited_ports=most_visited,
        total_ports=len(port_visit_counts)
    )

@app.route('/api/ports')
@login_required
def api_ports():
    ports = Port.query.order_by(Port.country, Port.name).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'city': p.city,
        'country': p.country,
        'lat': p.latitude,
        'lng': p.longitude
    } for p in ports])

@app.route('/api/cruise_ports/<int:cruise_id>')
@login_required
def api_cruise_ports(cruise_id):
    cruise = CruiseHistory.query.get_or_404(cruise_id)
    if cruise.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    cruise_ports = CruisePort.query.filter_by(cruise_id=cruise_id)\
        .order_by(CruisePort.visit_order).all()
    return jsonify([{
        'id': cp.id,
        'port_id': cp.port_id,
        'port_name': cp.port.name,
        'country': cp.port.country,
        'visit_order': cp.visit_order
    } for cp in cruise_ports])

@app.route('/add_port', methods=['POST'])
@login_required
def add_port():
    name = request.form['name']
    city = request.form.get('city', '')
    country = request.form['country']
    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])

    port = Port(name=name, city=city if city else None, country=country,
                latitude=latitude, longitude=longitude)
    db.session.add(port)
    db.session.commit()
    return jsonify({'id': port.id, 'name': port.name})

@app.route('/cruise_photos/<int:cruise_id>')
@login_required
def cruise_photos(cruise_id):
    cruise = CruiseHistory.query.get_or_404(cruise_id)
    if cruise.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    photos = CruisePhoto.query.filter_by(cruise_id=cruise_id).all()
    return jsonify([{
        'id': p.id,
        'filename': p.filename,
        'original_filename': p.original_filename,
        'is_cover': p.is_cover,
        'caption': p.caption,
        'url': f'/static/uploads/cruise_photos/{p.filename}'
    } for p in photos])

@app.route('/upload_photos/<int:cruise_id>', methods=['POST'])
@login_required
def upload_photos(cruise_id):
    cruise = CruiseHistory.query.get_or_404(cruise_id)
    if cruise.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    files = request.files.getlist('photos')
    uploaded = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{cruise_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            photo = CruisePhoto(
                cruise_id=cruise_id,
                filename=unique_filename,
                original_filename=filename
            )
            db.session.add(photo)
            uploaded.append({
                'filename': unique_filename,
                'original': filename
            })

    db.session.commit()
    return jsonify({'uploaded': uploaded, 'count': len(uploaded)})

@app.route('/set_cover_photo/<int:photo_id>', methods=['POST'])
@login_required
def set_cover_photo(photo_id):
    photo = CruisePhoto.query.get_or_404(photo_id)
    cruise = photo.cruise
    if cruise.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Remove existing cover
    CruisePhoto.query.filter_by(cruise_id=cruise.cruiseid, is_cover=True).update({'is_cover': False})
    photo.is_cover = True
    db.session.commit()
    return jsonify({'success': True, 'photo_id': photo_id})

@app.route('/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = CruisePhoto.query.get_or_404(photo_id)
    if photo.cruise.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Delete file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(photo)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if password != confirm:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful!')
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)