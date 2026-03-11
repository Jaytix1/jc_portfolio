from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
import os
import re
import sys

# Fix dual-module issue: when running as __main__, register as Histacruise.app
# so that 'from Histacruise.app import db' returns the same module instance.
if __name__ == '__main__':
    sys.modules['Histacruise.app'] = sys.modules['__main__']

app = Flask(__name__)


# ============== VALIDATION CONSTANTS ==============

# Cruise duration limits
MIN_CRUISE_NIGHTS = 1
MAX_CRUISE_NIGHTS = 180
WARN_CRUISE_NIGHTS = 30  # Warn if cruise is longer than this

# Cost limits
MIN_COST = 0
MAX_COST = 100000
WARN_COST = 20000  # Warn if cost exceeds this

# Rating limits
MIN_RATING = 1
MAX_RATING = 5

# Budget limits
MIN_BUDGET = 0
MAX_BUDGET = 500000

# Port coordinate limits
MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180

# Text field limits
MAX_CABIN_NUMBER_LENGTH = 10
MAX_DECK_LENGTH = 20
MAX_NOTES_LENGTH = 5000
MAX_PORT_NAME_LENGTH = 100

# Photo limits
MAX_PHOTOS_PER_CRUISE = 50

# Date limits
MAX_FUTURE_YEARS = 2  # Can't add cruises more than 2 years in the future

# Cabin types
CABIN_TYPES = [
    ('interior', 'Interior'),
    ('oceanview', 'Ocean View'),
    ('balcony', 'Balcony'),
    ('suite', 'Suite'),
    ('haven', 'Haven/Luxury Suite'),
    ('studio', 'Studio (Solo)')
]

# Social feature limits
MAX_POST_CONTENT_LENGTH = 2000
MAX_COMMENT_LENGTH = 1000
MAX_BIO_LENGTH = 500
MAX_DISPLAY_NAME_LENGTH = 100
MAX_LOCATION_LENGTH = 255
MAX_HASHTAGS_LENGTH = 500
MAX_HOMETOWN_LENGTH = 255
SOCIAL_POSTS_PER_PAGE = 20
NOTIFICATIONS_PER_PAGE = 30
DISCOVER_USERS_PER_PAGE = 20

# Reaction types for posts
REACTION_TYPES = {
    'heart': '❤️',
    'love': '😍',
    'funny': '😂',
    'wow': '😮',
    'jealous': '🤩',
}

# Achievement badge definitions
BADGE_DEFINITIONS = {
    'first_voyage': {'name': 'First Voyage', 'icon': '⛵', 'description': 'Completed your first cruise'},
    'sea_legs': {'name': 'Sea Legs', 'icon': '🚢', 'description': 'Completed 5 cruises'},
    'admiral': {'name': 'Admiral', 'icon': '⚓', 'description': 'Completed 15 cruises'},
    'week_at_sea': {'name': 'Week at Sea', 'icon': '🌊', 'description': 'Took a 7+ night cruise'},
    'month_at_sea': {'name': 'Month at Sea', 'icon': '🗓️', 'description': 'Spent 30+ total days at sea'},
    'century_sailor': {'name': 'Century Sailor', 'icon': '💯', 'description': 'Spent 100+ total days at sea'},
    'ship_hopper': {'name': 'Ship Hopper', 'icon': '🔄', 'description': 'Sailed on 3+ different ships'},
    'globe_trotter': {'name': 'Globe Trotter', 'icon': '🌍', 'description': 'Cruised in 3+ regions'},
    'world_explorer': {'name': 'World Explorer', 'icon': '🗺️', 'description': 'Cruised in 5+ regions'},
    'social_butterfly': {'name': 'Social Butterfly', 'icon': '🦋', 'description': 'Created 10+ posts'},
    'popular': {'name': 'Popular', 'icon': '⭐', 'description': 'Received 25+ reactions on your posts'},
    'storyteller': {'name': 'Storyteller', 'icon': '📖', 'description': 'Received 10+ comments on your posts'},
}


# ============== VALIDATION FUNCTIONS ==============

def validate_cruise_dates(begindate, enddate):
    """Validate cruise dates and return (is_valid, errors, warnings)."""
    errors = []
    warnings = []

    # Check end date is after begin date
    if enddate <= begindate:
        errors.append("End date must be after begin date.")
        return False, errors, warnings

    # Calculate duration
    duration = (enddate - begindate).days

    # Check minimum duration
    if duration < MIN_CRUISE_NIGHTS:
        errors.append(f"Cruise must be at least {MIN_CRUISE_NIGHTS} night(s).")

    # Check maximum duration
    if duration > MAX_CRUISE_NIGHTS:
        errors.append(f"Cruise duration cannot exceed {MAX_CRUISE_NIGHTS} nights. You entered {duration} nights.")

    # Warning for long cruises
    if duration > WARN_CRUISE_NIGHTS and duration <= MAX_CRUISE_NIGHTS:
        warnings.append(f"This is a {duration}-night cruise. Please verify this is correct.")

    # Check not too far in the future
    max_future_date = datetime.now().date() + timedelta(days=MAX_FUTURE_YEARS * 365)
    if begindate > max_future_date:
        errors.append(f"Cruise begin date cannot be more than {MAX_FUTURE_YEARS} years in the future.")

    return len(errors) == 0, errors, warnings


def validate_ship_cruiseline(ship_id, cruiseline_id):
    """Validate that the ship belongs to the selected cruise line."""
    ship = Ship.query.get(ship_id)
    if not ship:
        return False, "Invalid ship selected."

    if ship.cruiseline_id != int(cruiseline_id):
        cruiseline = CruiseLine.query.get(cruiseline_id)
        return False, f"'{ship.name}' does not belong to {cruiseline.name if cruiseline else 'the selected cruise line'}. Please select a ship from {cruiseline.name if cruiseline else 'the correct cruise line'}."

    return True, None


def validate_cost(cost):
    """Validate cruise cost and return (is_valid, error, warning)."""
    if cost is None:
        return True, None, None

    try:
        cost = float(cost)
    except (ValueError, TypeError):
        return False, "Cost must be a valid number.", None

    if cost < MIN_COST:
        return False, "Cost cannot be negative.", None

    if cost > MAX_COST:
        return False, f"Cost cannot exceed ${MAX_COST:,}. Please verify the amount.", None

    warning = None
    if cost > WARN_COST:
        warning = f"Cost of ${cost:,.2f} is unusually high. Please verify this is correct."

    return True, None, warning


def validate_rating(rating):
    """Validate cruise rating."""
    if rating is None or rating == '':
        return True, None

    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return False, "Rating must be a whole number."

    if rating < MIN_RATING or rating > MAX_RATING:
        return False, f"Rating must be between {MIN_RATING} and {MAX_RATING} stars."

    return True, None


def validate_budget(budget):
    """Validate yearly budget."""
    if budget is None:
        return True, None

    try:
        budget = float(budget)
    except (ValueError, TypeError):
        return False, "Budget must be a valid number."

    if budget < MIN_BUDGET:
        return False, "Budget cannot be negative."

    if budget > MAX_BUDGET:
        return False, f"Budget cannot exceed ${MAX_BUDGET:,}."

    return True, None


def validate_port_coordinates(latitude, longitude):
    """Validate port coordinates are realistic."""
    errors = []

    try:
        lat = float(latitude)
        lng = float(longitude)
    except (ValueError, TypeError):
        return False, ["Coordinates must be valid numbers."]

    if lat < MIN_LATITUDE or lat > MAX_LATITUDE:
        errors.append(f"Latitude must be between {MIN_LATITUDE} and {MAX_LATITUDE}.")

    if lng < MIN_LONGITUDE or lng > MAX_LONGITUDE:
        errors.append(f"Longitude must be between {MIN_LONGITUDE} and {MAX_LONGITUDE}.")

    return len(errors) == 0, errors


def validate_text_field(value, field_name, max_length):
    """Validate text field length."""
    if value is None or value == '':
        return True, None

    if len(value) > max_length:
        return False, f"{field_name} cannot exceed {max_length} characters."

    return True, None


def sanitize_text(text):
    """Basic text sanitization to prevent XSS."""
    if text is None:
        return None
    # Remove any script tags and dangerous patterns
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    return text.strip()

# Use absolute path for database to ensure consistency
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-fallback-key')
_db_url = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "instance", "histacruise.db")}')
# SQLAlchemy requires postgresql:// not postgres:// (Supabase/Render may give postgres://)
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,   # test connection before use, discard stale ones
    'pool_recycle': 280,     # recycle connections before Supabase's 300s idle timeout
    'pool_timeout': 30,
    'connect_args': {'connect_timeout': 10},
}

# Photo upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

MIMETYPE_MAP = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_mimetype(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return MIMETYPE_MAP.get(ext, 'application/octet-stream')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
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
    countdown_cruise_id = db.Column(db.Integer, db.ForeignKey('cruise_history.cruiseid'), nullable=True)

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

    # Optional fields
    cabin_number = db.Column(db.String(20), nullable=True)
    cabin_type = db.Column(db.String(30), nullable=True)  # interior, oceanview, balcony, suite, etc.
    deck = db.Column(db.String(50), nullable=True)
    cost = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    visibility = db.Column(db.String(20), nullable=False, server_default='public')
    
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
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mimetype = db.Column(db.String(50), nullable=True)
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


# ============== SOCIAL / COMMUNITY MODELS ==============

class SocialProfile(db.Model):
    __tablename__ = 'social_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_filename = db.Column(db.String(255), nullable=True)
    avatar_data = db.Column(db.LargeBinary, nullable=True)
    avatar_mimetype = db.Column(db.String(50), nullable=True)
    cover_filename = db.Column(db.String(255), nullable=True)
    cover_data = db.Column(db.LargeBinary, nullable=True)
    cover_mimetype = db.Column(db.String(50), nullable=True)
    hometown = db.Column(db.String(255), nullable=True)
    sailing_status = db.Column(db.String(30), nullable=True)
    sailing_status_cruise_id = db.Column(db.Integer, db.ForeignKey('cruise_history.cruiseid'), nullable=True)
    favorite_cruise_id = db.Column(db.Integer, db.ForeignKey('cruise_history.cruiseid'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('social_profile', uselist=False))
    sailing_status_cruise = db.relationship('CruiseHistory', foreign_keys=[sailing_status_cruise_id])
    favorite_cruise = db.relationship('CruiseHistory', foreign_keys=[favorite_cruise_id])

    def __repr__(self):
        return f'<SocialProfile user_id={self.user_id}>'


class SocialPost(db.Model):
    __tablename__ = 'social_post'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mimetype = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    hashtags = db.Column(db.String(500), nullable=True)
    shared_cruise_id = db.Column(db.Integer, db.ForeignKey('cruise_history.cruiseid', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='social_posts')
    shared_cruise = db.relationship('CruiseHistory', backref='social_shares')
    likes = db.relationship('PostLike', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    reactions = db.relationship('PostReaction', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('PostComment', backref='post', lazy='dynamic',
                               order_by='PostComment.created_at.asc()', cascade='all, delete-orphan')

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def reaction_count(self):
        return self.reactions.count()

    @property
    def comment_count(self):
        return self.comments.count()

    def is_liked_by(self, user):
        return self.likes.filter_by(user_id=user.id).first() is not None

    def user_reaction(self, user):
        r = self.reactions.filter_by(user_id=user.id).first()
        return r.reaction_type if r else None

    def reaction_summary(self):
        from sqlalchemy import func
        results = db.session.query(
            PostReaction.reaction_type, func.count(PostReaction.id)
        ).filter_by(post_id=self.id).group_by(PostReaction.reaction_type).all()
        return {r_type: count for r_type, count in results}

    def __repr__(self):
        return f'<SocialPost {self.id} by user {self.user_id}>'


class PostLike(db.Model):
    __tablename__ = 'post_like'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('social_post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='post_likes')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
    )

    def __repr__(self):
        return f'<PostLike user={self.user_id} post={self.post_id}>'


class PostComment(db.Model):
    __tablename__ = 'post_comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('social_post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='post_comments')

    def __repr__(self):
        return f'<PostComment {self.id} on post {self.post_id}>'


class UserFollow(db.Model):
    __tablename__ = 'user_follow'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # status: 'pending' (friend request sent) or 'accepted' (friends)
    status = db.Column(db.String(20), nullable=False, server_default='accepted')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship('User', foreign_keys=[follower_id], backref='following_assocs')
    following = db.relationship('User', foreign_keys=[following_id], backref='follower_assocs')

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'following_id', name='unique_user_follow'),
    )

    def __repr__(self):
        return f'<UserFollow {self.follower_id} -> {self.following_id} [{self.status}]>'


class UserBlock(db.Model):
    __tablename__ = 'user_block'

    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    blocker = db.relationship('User', foreign_keys=[blocker_id], backref='blocked_assocs')
    blocked = db.relationship('User', foreign_keys=[blocked_id], backref='blocked_by_assocs')

    __table_args__ = (
        db.UniqueConstraint('blocker_id', 'blocked_id', name='unique_user_block'),
    )

    def __repr__(self):
        return f'<UserBlock {self.blocker_id} -> {self.blocked_id}>'


class PostReaction(db.Model):
    __tablename__ = 'post_reaction'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('social_post.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='post_reactions')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_reaction'),
    )

    def __repr__(self):
        return f'<PostReaction {self.user_id} {self.reaction_type} on {self.post_id}>'


class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('social_post.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    actor = db.relationship('User', foreign_keys=[actor_id])
    post = db.relationship('SocialPost', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.type} for user {self.user_id}>'


class UserBadge(db.Model):
    __tablename__ = 'user_badge'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_type = db.Column(db.String(50), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='badges')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'badge_type', name='unique_user_badge'),
    )

    def __repr__(self):
        return f'<UserBadge {self.badge_type} for user {self.user_id}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if _db_url.startswith('sqlite'):
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
with app.app_context():
    try:
        db.create_all()  # Creates tables for fresh deployments; use `flask db upgrade` for migrations

        # Safe column additions — ignored if column already exists
        _migrations = [
            "ALTER TABLE user_follow ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'accepted'",
            "ALTER TABLE cruise_history ADD COLUMN visibility VARCHAR(20) NOT NULL DEFAULT 'public'",
            "ALTER TABLE user_preference ADD COLUMN IF NOT EXISTS countdown_cruise_id INTEGER REFERENCES cruise_history(cruiseid)",
        ]
        for _sql in _migrations:
            try:
                db.session.execute(db.text(_sql))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # Auto-seed reference data on first run (no-op if already populated)
        if CruiseLine.query.count() == 0:
            try:
                from reference_data import CRUISE_LINES, SHIPS, REGIONS, PORTS
                _lines = {}
                for _name in CRUISE_LINES:
                    _cl = CruiseLine.query.filter_by(name=_name).first()
                    if not _cl:
                        _cl = CruiseLine(name=_name)
                        db.session.add(_cl)
                        db.session.flush()
                    _lines[_name] = _cl
                for _line_name, _ship_names in SHIPS.items():
                    for _ship_name in _ship_names:
                        if not Ship.query.filter_by(name=_ship_name, cruiseline_id=_lines[_line_name].id).first():
                            db.session.add(Ship(name=_ship_name, cruiseline_id=_lines[_line_name].id))
                for _rname in REGIONS:
                    if not Region.query.filter_by(name=_rname).first():
                        db.session.add(Region(name=_rname))
                for _pname, _city, _country, _lat, _lon in PORTS:
                    if not Port.query.filter_by(name=_pname).first():
                        db.session.add(Port(name=_pname, city=_city, country=_country,
                                            latitude=_lat, longitude=_lon))
                db.session.commit()
                print('[Startup] Reference data seeded.')
            except Exception as _e:
                db.session.rollback()
                print(f'[Startup] Reference data seed failed: {_e}')
    except Exception as _startup_err:
        # DB unreachable during gunicorn's import phase (e.g. IPv6-only on free tier).
        # Tables already exist from prior deploys; runtime connections will work normally.
        print(f'[Startup] DB init skipped (will connect on first request): {_startup_err}')

# Register Pipeline API blueprint
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Gunicorn imports this module as 'app', but social routes import from 'Histacruise.app'.
# Alias them to the same module so Python doesn't import app.py a second time.
sys.modules.setdefault('Histacruise.app', sys.modules[__name__])
from HC_Pipeline.api.routes import pipeline_api
app.register_blueprint(pipeline_api)

# Register Social Community blueprint
from Histacruise.social import social_bp
app.register_blueprint(social_bp)

# ── Lazy DB init ──────────────────────────────────────────────────────────────
# db.create_all() at module level fails on Render free tier (IPv6 unreachable
# during gunicorn's import phase). Instead we run it on the first request, when
# the worker process is fully running and the network is available.
_db_initialized = False

@app.before_request
def _lazy_db_init():
    global _db_initialized
    if _db_initialized:
        return
    _db_initialized = True
    try:
        db.create_all()
        _lazy_migrations = [
            "ALTER TABLE user_follow ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'accepted'",
            "ALTER TABLE cruise_history ADD COLUMN visibility VARCHAR(20) NOT NULL DEFAULT 'public'",
            "ALTER TABLE user_preference ADD COLUMN IF NOT EXISTS countdown_cruise_id INTEGER REFERENCES cruise_history(cruiseid)",
        ]
        for _sql in _lazy_migrations:
            try:
                db.session.execute(db.text(_sql))
                db.session.commit()
            except Exception:
                db.session.rollback()
        if CruiseLine.query.count() == 0:
            from reference_data import CRUISE_LINES, SHIPS, REGIONS, PORTS
            _lines = {}
            for _name in CRUISE_LINES:
                _cl = CruiseLine.query.filter_by(name=_name).first()
                if not _cl:
                    _cl = CruiseLine(name=_name)
                    db.session.add(_cl)
                    db.session.flush()
                _lines[_name] = _cl
            for _line_name, _ship_names in SHIPS.items():
                for _ship_name in _ship_names:
                    if not Ship.query.filter_by(name=_ship_name, cruiseline_id=_lines[_line_name].id).first():
                        db.session.add(Ship(name=_ship_name, cruiseline_id=_lines[_line_name].id))
            for _rname in REGIONS:
                if not Region.query.filter_by(name=_rname).first():
                    db.session.add(Region(name=_rname))
            for _pname, _city, _country, _lat, _lon in PORTS:
                if not Port.query.filter_by(name=_pname).first():
                    db.session.add(Port(name=_pname, city=_city, country=_country,
                                        latitude=_lat, longitude=_lon))
            db.session.commit()
            print('[DB] Reference data seeded.')
        print('[DB] Init complete.')
    except Exception as _lazy_err:
        _db_initialized = False  # retry on next request
        db.session.rollback()
        print(f'[DB] Init failed, will retry: {_lazy_err}')

@app.route('/uploads/<category>/<filename>')
def serve_upload(category, filename):
    """Serve uploaded images from the database."""
    if category == 'profile_photos':
        record = SocialProfile.query.filter_by(avatar_filename=filename).first()
        if record and record.avatar_data:
            resp = make_response(record.avatar_data)
            resp.headers['Content-Type'] = record.avatar_mimetype or 'image/jpeg'
            resp.headers['Cache-Control'] = 'public, max-age=86400'
            return resp
    elif category == 'cover_photos':
        record = SocialProfile.query.filter_by(cover_filename=filename).first()
        if record and record.cover_data:
            resp = make_response(record.cover_data)
            resp.headers['Content-Type'] = record.cover_mimetype or 'image/jpeg'
            resp.headers['Cache-Control'] = 'public, max-age=86400'
            return resp
    elif category == 'social_photos':
        record = SocialPost.query.filter_by(image_filename=filename).first()
        if record and record.image_data:
            resp = make_response(record.image_data)
            resp.headers['Content-Type'] = record.image_mimetype or 'image/jpeg'
            resp.headers['Cache-Control'] = 'public, max-age=86400'
            return resp
    elif category == 'cruise_photos':
        record = CruisePhoto.query.filter_by(filename=filename).first()
        if record and record.image_data:
            resp = make_response(record.image_data)
            resp.headers['Content-Type'] = record.image_mimetype or 'image/jpeg'
            resp.headers['Cache-Control'] = 'public, max-age=86400'
            return resp
    return '', 404


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

    # Cruise countdown
    countdown_cruise = None
    countdown_days = None
    if current_user.is_authenticated and current_user.preferences and current_user.preferences.countdown_cruise_id:
        from datetime import date
        cc = CruiseHistory.query.get(current_user.preferences.countdown_cruise_id)
        if cc and cc.begindate > date.today():
            countdown_cruise = cc
            countdown_days = (cc.begindate - date.today()).days

    return render_template('home.html',
                          stocks=stocks_data,
                          chart_data=chart_data,
                          news=news,
                          deals=deals,
                          countdown_cruise=countdown_cruise,
                          countdown_days=countdown_days)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add_cruise', methods=['POST'])
@login_required
def add_cruise():
    errors = []
    warnings = []

    # Get form data
    begindate = request.form.get('begindate')
    enddate = request.form.get('enddate')
    cruiseline_id = request.form.get('cruiseline_id')
    ship_id = request.form.get('ship_id')
    region_id = request.form.get('region_id')

    # Optional fields
    cabin_number = request.form.get('cabin_number', '').strip()
    cabin_type = request.form.get('cabin_type', '').strip()
    deck = request.form.get('deck', '').strip()
    cost = request.form.get('cost', None)
    notes = request.form.get('notes', '').strip()
    rating = request.form.get('rating', None)
    visibility = request.form.get('visibility', 'public')
    if visibility not in ('public', 'followers', 'private'):
        visibility = 'public'

    # Validate required fields
    if not all([begindate, enddate, cruiseline_id, ship_id, region_id]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('history'))

    # Parse dates
    try:
        begindate_obj = datetime.strptime(begindate, '%Y-%m-%d').date()
        enddate_obj = datetime.strptime(enddate, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('history'))

    # Validate dates
    dates_valid, date_errors, date_warnings = validate_cruise_dates(begindate_obj, enddate_obj)
    errors.extend(date_errors)
    warnings.extend(date_warnings)

    # Validate ship belongs to cruise line
    ship_valid, ship_error = validate_ship_cruiseline(ship_id, cruiseline_id)
    if not ship_valid:
        errors.append(ship_error)

    # Validate cost
    if cost and cost.strip():
        cost_valid, cost_error, cost_warning = validate_cost(cost)
        if not cost_valid:
            errors.append(cost_error)
        if cost_warning:
            warnings.append(cost_warning)
        cost = float(cost) if cost_valid and cost.strip() else None
    else:
        cost = None

    # Validate rating
    if rating and rating.strip():
        rating_valid, rating_error = validate_rating(rating)
        if not rating_valid:
            errors.append(rating_error)
        rating = int(rating) if rating_valid and rating.strip() else None
    else:
        rating = None

    # Validate text fields
    cabin_valid, cabin_error = validate_text_field(cabin_number, 'Cabin number', MAX_CABIN_NUMBER_LENGTH)
    if not cabin_valid:
        errors.append(cabin_error)

    deck_valid, deck_error = validate_text_field(deck, 'Deck', MAX_DECK_LENGTH)
    if not deck_valid:
        errors.append(deck_error)

    notes_valid, notes_error = validate_text_field(notes, 'Notes', MAX_NOTES_LENGTH)
    if not notes_valid:
        errors.append(notes_error)

    # Sanitize text inputs
    cabin_number = sanitize_text(cabin_number)
    deck = sanitize_text(deck)
    notes = sanitize_text(notes)

    # Validate cabin type if provided
    if cabin_type and cabin_type not in [ct[0] for ct in CABIN_TYPES]:
        errors.append("Invalid cabin type selected.")

    # If there are errors, flash them and redirect
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('history'))

    # Show warnings but continue
    for warning in warnings:
        flash(warning, 'warning')

    # Create the cruise
    new_cruise = CruiseHistory(
        begindate=begindate_obj,
        enddate=enddate_obj,
        cruiseline_id=cruiseline_id,
        ship_id=ship_id,
        region_id=region_id,
        cabin_number=cabin_number if cabin_number else None,
        cabin_type=cabin_type if cabin_type else None,
        deck=deck if deck else None,
        cost=cost,
        notes=notes if notes else None,
        rating=rating,
        visibility=visibility,
        user_id=current_user.id
    )

    db.session.add(new_cruise)
    db.session.flush()  # Get the cruise ID before committing

    # Handle ports - check for duplicates
    port_ids = request.form.getlist('port_ids[]')
    seen_ports = set()
    for order, port_id in enumerate(port_ids, 1):
        if port_id:
            if port_id in seen_ports:
                flash(f'Duplicate port removed from itinerary.', 'warning')
                continue
            seen_ports.add(port_id)
            cruise_port = CruisePort(
                cruise_id=new_cruise.cruiseid,
                port_id=int(port_id),
                visit_order=order
            )
            db.session.add(cruise_port)

    # Handle photo uploads
    photos = request.files.getlist('photos')
    photo_count = 0
    for file in photos:
        if file and file.filename and allowed_file(file.filename):
            if photo_count >= MAX_PHOTOS_PER_CRUISE:
                break
            filename = secure_filename(file.filename)
            unique_filename = f"{new_cruise.cruiseid}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
            file_data = file.read()
            mimetype = get_mimetype(filename)
            photo = CruisePhoto(
                cruise_id=new_cruise.cruiseid,
                filename=unique_filename,
                original_filename=filename,
                image_data=file_data,
                image_mimetype=mimetype,
                is_cover=(photo_count == 0)
            )
            db.session.add(photo)
            photo_count += 1

    db.session.commit()

    flash('Cruise added successfully!', 'success')
    from datetime import date
    if new_cruise.begindate > date.today():
        return redirect(url_for('history', prompt_countdown=new_cruise.cruiseid))
    return redirect(url_for('history'))

@app.route('/delete_cruise/<int:cruise_id>', methods=['POST'])
@login_required
def delete_cruise(cruise_id):
    cruise = CruiseHistory.query.get_or_404(cruise_id)

    # Make sure the cruise belongs to the current user
    if cruise.user_id != current_user.id:
        flash('You do not have permission to delete this cruise.', 'error')
        return redirect(url_for('history'))

    # Delete associated photos (DB records — BLOB data deleted automatically)
    CruisePhoto.query.filter_by(cruise_id=cruise_id).delete()

    # Delete associated cruise ports
    CruisePort.query.filter_by(cruise_id=cruise_id).delete()

    # Delete the cruise
    db.session.delete(cruise)
    db.session.commit()

    flash('Cruise and all associated data deleted successfully!', 'success')
    return redirect(url_for('history'))

@app.route('/edit_cruise/<int:cruise_id>', methods=['POST'])
@login_required
def edit_cruise(cruise_id):
    cruise = CruiseHistory.query.get_or_404(cruise_id)

    if cruise.user_id != current_user.id:
        flash('You do not have permission to edit this cruise.', 'error')
        return redirect(url_for('history'))

    errors = []
    warnings = []

    # Get form data
    begindate = request.form.get('begindate')
    enddate = request.form.get('enddate')
    cruiseline_id = request.form.get('cruiseline_id')
    ship_id = request.form.get('ship_id')
    region_id = request.form.get('region_id')

    # Optional fields
    cabin_number = request.form.get('cabin_number', '').strip()
    cabin_type = request.form.get('cabin_type', '').strip()
    deck = request.form.get('deck', '').strip()
    cost = request.form.get('cost', None)
    notes = request.form.get('notes', '').strip()
    rating = request.form.get('rating', None)
    visibility = request.form.get('visibility', 'public')
    if visibility not in ('public', 'followers', 'private'):
        visibility = 'public'

    # Validate required fields
    if not all([begindate, enddate, cruiseline_id, ship_id, region_id]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('history'))

    # Parse dates
    try:
        begindate_obj = datetime.strptime(begindate, '%Y-%m-%d').date()
        enddate_obj = datetime.strptime(enddate, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('history'))

    # Validate dates
    dates_valid, date_errors, date_warnings = validate_cruise_dates(begindate_obj, enddate_obj)
    errors.extend(date_errors)
    warnings.extend(date_warnings)

    # Validate ship belongs to cruise line
    ship_valid, ship_error = validate_ship_cruiseline(ship_id, cruiseline_id)
    if not ship_valid:
        errors.append(ship_error)

    # Validate cost
    if cost and cost.strip():
        cost_valid, cost_error, cost_warning = validate_cost(cost)
        if not cost_valid:
            errors.append(cost_error)
        if cost_warning:
            warnings.append(cost_warning)
        cost = float(cost) if cost_valid and cost.strip() else None
    else:
        cost = None

    # Validate rating
    if rating and rating.strip():
        rating_valid, rating_error = validate_rating(rating)
        if not rating_valid:
            errors.append(rating_error)
        rating = int(rating) if rating_valid and rating.strip() else None
    else:
        rating = None

    # Validate text fields
    cabin_valid, cabin_error = validate_text_field(cabin_number, 'Cabin number', MAX_CABIN_NUMBER_LENGTH)
    if not cabin_valid:
        errors.append(cabin_error)

    deck_valid, deck_error = validate_text_field(deck, 'Deck', MAX_DECK_LENGTH)
    if not deck_valid:
        errors.append(deck_error)

    notes_valid, notes_error = validate_text_field(notes, 'Notes', MAX_NOTES_LENGTH)
    if not notes_valid:
        errors.append(notes_error)

    # Sanitize text inputs
    cabin_number = sanitize_text(cabin_number)
    deck = sanitize_text(deck)
    notes = sanitize_text(notes)

    # Validate cabin type if provided
    if cabin_type and cabin_type not in [ct[0] for ct in CABIN_TYPES]:
        errors.append("Invalid cabin type selected.")

    # If there are errors, flash them and redirect
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('history'))

    # Show warnings but continue
    for warning in warnings:
        flash(warning, 'warning')

    # Update the cruise
    cruise.begindate = begindate_obj
    cruise.enddate = enddate_obj
    cruise.cruiseline_id = cruiseline_id
    cruise.ship_id = ship_id
    cruise.region_id = region_id
    cruise.cabin_number = cabin_number if cabin_number else None
    cruise.cabin_type = cabin_type if cabin_type else None
    cruise.deck = deck if deck else None
    cruise.cost = cost
    cruise.notes = notes if notes else None
    cruise.rating = rating
    cruise.visibility = visibility

    # Handle ports - remove old ones and add new (with duplicate check)
    CruisePort.query.filter_by(cruise_id=cruise_id).delete()
    port_ids = request.form.getlist('port_ids[]')
    seen_ports = set()
    for order, port_id in enumerate(port_ids, 1):
        if port_id:
            if port_id in seen_ports:
                flash(f'Duplicate port removed from itinerary.', 'warning')
                continue
            seen_ports.add(port_id)
            cruise_port = CruisePort(
                cruise_id=cruise_id,
                port_id=int(port_id),
                visit_order=order
            )
            db.session.add(cruise_port)

    db.session.commit()

    flash('Cruise updated successfully!', 'success')
    return redirect(url_for('history'))

@app.route('/history')
@login_required
def history():
    cruises = CruiseHistory.query.filter_by(user_id=current_user.id).all()
    cruiselines = CruiseLine.query.order_by(CruiseLine.name).all()
    ships = Ship.query.order_by(Ship.name).all()
    regions = Region.query.order_by(Region.name).all()
    ports = Port.query.order_by(Port.country, Port.name).all()

    prompt_countdown = request.args.get('prompt_countdown', type=int)
    current_countdown_id = (current_user.preferences.countdown_cruise_id
                            if current_user.preferences else None)

    return render_template('history.html',
                           cruises=cruises,
                           cruiselines=cruiselines,
                           ships=ships,
                           regions=regions,
                           ports=ports,
                           cabin_types=CABIN_TYPES,
                           prompt_countdown=prompt_countdown,
                           current_countdown_id=current_countdown_id)

@app.route('/statistics')
@login_required
def statistics():
    cruises = CruiseHistory.query.filter_by(user_id=current_user.id).all()

    # Initialize counters
    cruiseline_counts = {}
    region_counts = {}
    ship_counts = {}
    cabin_type_counts = {}
    total_days = 0
    total_cost = 0
    cruises_with_cost = 0
    cruises_by_year = {}
    cost_by_year = {}
    cost_by_cruiseline = {}

    # Missing data tracking
    missing_cost_ids = []
    missing_cabin_type_ids = []
    missing_rating_ids = []
    days_with_cost = 0

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

        # Cabin type counts
        if cruise.cabin_type:
            cabin_type_label = dict(CABIN_TYPES).get(cruise.cabin_type, cruise.cabin_type)
            cabin_type_counts[cabin_type_label] = cabin_type_counts.get(cabin_type_label, 0) + 1
        else:
            missing_cabin_type_ids.append(cruise.cruiseid)

        # Days calculation
        delta = cruise.enddate - cruise.begindate
        cruise_days = delta.days
        total_days += cruise_days

        # Cost calculations
        if cruise.cost:
            total_cost += cruise.cost
            cruises_with_cost += 1
            days_with_cost += cruise_days
            if line_name not in cost_by_cruiseline:
                cost_by_cruiseline[line_name] = {'total': 0, 'count': 0}
            cost_by_cruiseline[line_name]['total'] += cruise.cost
            cost_by_cruiseline[line_name]['count'] += 1
        else:
            missing_cost_ids.append(cruise.cruiseid)

        # Year-based aggregation
        year = cruise.begindate.year
        cruises_by_year[year] = cruises_by_year.get(year, 0) + 1
        if cruise.cost:
            cost_by_year[year] = cost_by_year.get(year, 0) + cruise.cost

        # Rating tracking
        if not cruise.rating:
            missing_rating_ids.append(cruise.cruiseid)

    # Derived statistics
    avg_cruise_length = total_days / len(cruises) if cruises else 0
    avg_cost = total_cost / cruises_with_cost if cruises_with_cost else 0
    avg_cost_per_day = total_cost / days_with_cost if days_with_cost and total_cost else 0

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
        cabin_type_counts=cabin_type_counts,
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
        budget_remaining=budget_remaining,
        missing_cost_count=len(missing_cost_ids),
        missing_cabin_type_count=len(missing_cabin_type_ids),
        missing_rating_count=len(missing_rating_ids),
        cruises_with_cost=cruises_with_cost,
        cruises_with_cabin_type=sum(cabin_type_counts.values())
    )

@app.route('/set_budget', methods=['POST'])
@login_required
def set_budget():
    budget = request.form.get('yearly_budget')

    # Handle empty budget (clearing)
    if not budget or budget.strip() == '':
        pref = UserPreference.query.filter_by(user_id=current_user.id).first()
        if pref:
            pref.yearly_budget = None
            db.session.commit()
        flash('Budget cleared.', 'success')
        return redirect(url_for('statistics'))

    # Validate budget
    budget_valid, budget_error = validate_budget(budget)
    if not budget_valid:
        flash(budget_error, 'error')
        return redirect(url_for('statistics'))

    budget = float(budget)

    pref = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.session.add(pref)
    pref.yearly_budget = budget
    db.session.commit()
    flash(f'Budget set to ${budget:,.2f}!', 'success')
    return redirect(url_for('statistics'))


@app.route('/clear_budget', methods=['POST'])
@login_required
def clear_budget():
    """Clear the yearly budget."""
    pref = UserPreference.query.filter_by(user_id=current_user.id).first()
    if pref:
        pref.yearly_budget = None
        db.session.commit()
    flash('Budget cleared.', 'success')
    return redirect(url_for('statistics'))

@app.route('/set_countdown', methods=['POST'])
@login_required
def set_countdown():
    cruise_id = request.form.get('cruise_id', type=int)  # None if missing/empty
    pref = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.session.add(pref)
    pref.countdown_cruise_id = cruise_id
    db.session.commit()
    return ('', 204)


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
    name = request.form.get('name', '').strip()
    city = request.form.get('city', '').strip()
    country = request.form.get('country', '').strip()
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    # Validate required fields
    if not name or not country:
        return jsonify({'error': 'Port name and country are required.'}), 400

    # Validate name length
    name_valid, name_error = validate_text_field(name, 'Port name', MAX_PORT_NAME_LENGTH)
    if not name_valid:
        return jsonify({'error': name_error}), 400

    # Validate coordinates
    if not latitude or not longitude:
        return jsonify({'error': 'Coordinates are required.'}), 400

    coords_valid, coord_errors = validate_port_coordinates(latitude, longitude)
    if not coords_valid:
        return jsonify({'error': ' '.join(coord_errors)}), 400

    # Check for duplicate port (same name and country)
    existing = Port.query.filter_by(name=name, country=country).first()
    if existing:
        return jsonify({'error': f'Port "{name}" in {country} already exists.', 'id': existing.id}), 409

    # Sanitize text
    name = sanitize_text(name)
    city = sanitize_text(city)
    country = sanitize_text(country)

    port = Port(
        name=name,
        city=city if city else None,
        country=country,
        latitude=float(latitude),
        longitude=float(longitude)
    )
    db.session.add(port)
    db.session.commit()
    return jsonify({'id': port.id, 'name': port.name, 'country': port.country})


@app.route('/api/ships/<int:cruiseline_id>')
@login_required
def api_ships_by_cruiseline(cruiseline_id):
    """Get ships belonging to a specific cruise line."""
    ships = Ship.query.filter_by(cruiseline_id=cruiseline_id).order_by(Ship.name).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'cruiseline_id': s.cruiseline_id
    } for s in ships])


@app.route('/api/validate_ship', methods=['POST'])
@login_required
def api_validate_ship():
    """Validate that a ship belongs to a cruise line."""
    data = request.get_json()
    ship_id = data.get('ship_id')
    cruiseline_id = data.get('cruiseline_id')

    if not ship_id or not cruiseline_id:
        return jsonify({'valid': False, 'error': 'Missing ship_id or cruiseline_id'})

    valid, error = validate_ship_cruiseline(ship_id, cruiseline_id)
    return jsonify({'valid': valid, 'error': error})

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
        'url': f'/uploads/cruise_photos/{p.filename}'
    } for p in photos])

@app.route('/upload_photos/<int:cruise_id>', methods=['POST'])
@login_required
def upload_photos(cruise_id):
    cruise = CruiseHistory.query.get_or_404(cruise_id)
    if cruise.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Check current photo count
    current_photo_count = CruisePhoto.query.filter_by(cruise_id=cruise_id).count()

    files = request.files.getlist('photos')

    # Validate photo limit
    if current_photo_count + len(files) > MAX_PHOTOS_PER_CRUISE:
        remaining = MAX_PHOTOS_PER_CRUISE - current_photo_count
        return jsonify({
            'error': f'Photo limit exceeded. You can only upload {remaining} more photo(s). Maximum is {MAX_PHOTOS_PER_CRUISE} per cruise.',
            'current_count': current_photo_count,
            'max_allowed': MAX_PHOTOS_PER_CRUISE
        }), 400

    uploaded = []
    skipped = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{cruise_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
            file_data = file.read()
            mimetype = get_mimetype(filename)

            photo = CruisePhoto(
                cruise_id=cruise_id,
                filename=unique_filename,
                original_filename=filename,
                image_data=file_data,
                image_mimetype=mimetype
            )
            db.session.add(photo)
            uploaded.append({
                'filename': unique_filename,
                'original': filename
            })
        elif file and file.filename:
            skipped.append({
                'filename': file.filename,
                'reason': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'
            })

    db.session.commit()
    return jsonify({
        'uploaded': uploaded,
        'count': len(uploaded),
        'skipped': skipped,
        'total_photos': current_photo_count + len(uploaded)
    })

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

        login_user(new_user)
        flash('Welcome to Histacruise!')
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

# ============== AUTOMATED PIPELINE SCHEDULER ==============

def setup_scheduler():
    """Set up APScheduler to run pipeline jobs automatically."""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    import atexit

    scheduler = BackgroundScheduler()

    def run_pipeline_job(job_type):
        """Run a specific pipeline job."""
        try:
            from HC_Pipeline.main import Pipeline
            pipeline = Pipeline(app)

            if job_type == 'stocks':
                pipeline.run_stocks()
            elif job_type == 'news':
                pipeline.run_news()
            elif job_type == 'deals':
                pipeline.run_deals()
            elif job_type == 'ships':
                pipeline.run_ships()

            print(f"[Scheduler] {job_type} pipeline completed at {datetime.now()}")
        except Exception as e:
            print(f"[Scheduler] {job_type} pipeline failed: {e}")

    # Schedule jobs:
    # - Stocks: Every 2 hours (market data updates)
    # - News: Every 3 hours
    # - Deals: Every 6 hours
    # - Ships: Once daily

    scheduler.add_job(
        func=lambda: run_pipeline_job('stocks'),
        trigger=IntervalTrigger(hours=2),
        id='stock_collector',
        name='Collect stock prices',
        replace_existing=True
    )

    scheduler.add_job(
        func=lambda: run_pipeline_job('news'),
        trigger=IntervalTrigger(hours=3),
        id='news_collector',
        name='Collect cruise news',
        replace_existing=True
    )

    scheduler.add_job(
        func=lambda: run_pipeline_job('deals'),
        trigger=IntervalTrigger(hours=6),
        id='deals_collector',
        name='Collect cruise deals',
        replace_existing=True
    )

    scheduler.add_job(
        func=lambda: run_pipeline_job('ships'),
        trigger=IntervalTrigger(hours=24),
        id='ship_collector',
        name='Collect ship specifications',
        replace_existing=True
    )

    scheduler.start()
    print("[Scheduler] Pipeline scheduler started!")
    print("  - Stocks: Every 2 hours")
    print("  - News: Every 3 hours")
    print("  - Deals: Every 6 hours")
    print("  - Ships: Every 24 hours")

    # Shut down scheduler when app exits
    atexit.register(lambda: scheduler.shutdown())

    return scheduler

# Start scheduler — runs under both gunicorn and direct python app.py
# Guard prevents double-start when Flask dev reloader forks a second process
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = setup_scheduler()

    # Run full pipeline on startup in background so data is ready immediately
    def _initial_pipeline_run():
        import time
        time.sleep(20)  # Wait for DB lazy-init to complete on first request
        try:
            from HC_Pipeline.main import Pipeline
            print('[Startup] Running initial pipeline...')
            pipeline = Pipeline(app)
            results = pipeline.run_all()
            print(f'[Startup] Pipeline complete: {results}')
        except Exception as e:
            print(f'[Startup] Pipeline failed: {e}')

    import threading
    threading.Thread(target=_initial_pipeline_run, daemon=True).start()

@app.route('/admin/run-pipeline')
@login_required
def admin_run_pipeline():
    """Manually trigger the full pipeline. Admin/owner use only."""
    def _run():
        try:
            from HC_Pipeline.main import Pipeline
            Pipeline(app).run_all()
        except Exception as e:
            print(f'[Admin] Pipeline run failed: {e}')
    import threading
    threading.Thread(target=_run, daemon=True).start()
    flash('Pipeline triggered — data will appear within a few minutes.')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)  # use_reloader=False prevents double scheduler