"""
Histacruise Seed Script
========================
Populates the database with realistic demo data for portfolio demonstrations.

Usage:
    python seed.py

Safe to run multiple times — skips creation if demo user already exists.

Demo credentials:
    Email:    demo@histacruise.com
    Password: Demo1234!
"""

import sys
import os

# Allow running from Histacruise/ directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app import (
    User, UserPreference, CruiseLine, Ship, Region,
    CruiseHistory, Port, CruisePort,
    SocialProfile, SocialPost, PostLike, PostComment, UserFollow,
)
from datetime import date, datetime


# ─── Reference Data ──────────────────────────────────────────────────────────

CRUISE_LINES = ['Royal Caribbean', 'Carnival Cruise Line', 'Norwegian Cruise Line',
                'Celebrity Cruises', 'Disney Cruise Line']

SHIPS = {
    'Royal Caribbean':       ['Wonder of the Seas', 'Symphony of the Seas', 'Oasis of the Seas'],
    'Carnival Cruise Line':  ['Carnival Sunshine', 'Carnival Celebration', 'Mardi Gras'],
    'Norwegian Cruise Line': ['Norwegian Escape', 'Norwegian Bliss', 'Norwegian Prima'],
    'Celebrity Cruises':     ['Celebrity Edge', 'Celebrity Apex', 'Celebrity Beyond'],
    'Disney Cruise Line':    ['Disney Wish', 'Disney Dream', 'Disney Magic'],
}

REGIONS = ['Caribbean', 'Mediterranean', 'Alaska', 'Bahamas',
           'Europe', 'Mexico', 'Hawaii', 'Bermuda']

PORTS = [
    ('Port of Miami',         'Miami',         'United States', 25.7742, -80.1747),
    ('Port Canaveral',        'Cape Canaveral','United States', 28.4158, -80.5917),
    ('Nassau Cruise Port',    'Nassau',        'Bahamas',       25.0833, -77.3500),
    ('Cozumel Pier',          'Cozumel',       'Mexico',        20.5088, -86.9517),
    ('St. Thomas WICO',       'Charlotte Amalie','US Virgin Islands',18.3381,-64.9307),
    ('Barcelona Cruise Port', 'Barcelona',     'Spain',         41.3614,   2.1731),
    ('Civitavecchia Port',    'Rome',          'Italy',         42.0941,  11.7962),
    ('Venice Cruise Terminal','Venice',        'Italy',         45.4408,  12.3155),
    ('Juneau',                'Juneau',        'United States', 58.3005,-134.4197),
    ('Skagway',               'Skagway',       'United States', 59.4583,-135.3139),
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_or_create(model, **kwargs):
    obj = model.query.filter_by(**kwargs).first()
    if not obj:
        obj = model(**kwargs)
        db.session.add(obj)
        db.session.flush()
    return obj


# ─── Seeders ─────────────────────────────────────────────────────────────────

def seed_reference_data():
    lines = {name: get_or_create(CruiseLine, name=name) for name in CRUISE_LINES}
    ships = {}
    for line_name, ship_names in SHIPS.items():
        for ship_name in ship_names:
            ship = get_or_create(Ship, name=ship_name, cruiseline_id=lines[line_name].id)
            ships[ship_name] = ship
    regions = {name: get_or_create(Region, name=name) for name in REGIONS}
    ports   = {}
    for name, city, country, lat, lon in PORTS:
        existing = Port.query.filter_by(name=name).first()
        if not existing:
            port = Port(name=name, city=city, country=country, latitude=lat, longitude=lon)
            db.session.add(port)
            db.session.flush()
        else:
            port = existing
        ports[name] = port
    db.session.commit()
    print('Reference data seeded.')
    return lines, ships, regions, ports


def seed_users():
    # Demo user
    demo = User.query.filter_by(email='demo@histacruise.com').first()
    if not demo:
        demo = User(username='cruise_explorer', email='demo@histacruise.com')
        demo.set_password('Demo1234!')
        db.session.add(demo)
        db.session.flush()
        pref = UserPreference(user_id=demo.id, dark_mode=False,
                              yearly_budget=8000.0, default_view='card')
        db.session.add(pref)

    # Second user for social interaction
    second = User.query.filter_by(email='sailor@histacruise.com').first()
    if not second:
        second = User(username='ocean_wanderer', email='sailor@histacruise.com')
        second.set_password('Demo1234!')
        db.session.add(second)
        db.session.flush()
        pref2 = UserPreference(user_id=second.id, dark_mode=False,
                               yearly_budget=12000.0, default_view='table')
        db.session.add(pref2)

    db.session.commit()
    print(f'Users seeded: {demo.username}, {second.username}')
    return demo, second


def seed_cruises(demo, second, lines, ships, regions):
    cruises = []

    cruise_data = [
        # Demo user's cruises
        (demo, 'Royal Caribbean', 'Symphony of the Seas', 'Caribbean',
         date(2023, 12, 9), date(2023, 12, 16), '8512', 'balcony', '10', 2199.0, 5,
         'Amazing holiday cruise! The ship was spectacular, entertainment every night.'),
        (demo, 'Norwegian Cruise Line', 'Norwegian Escape', 'Bahamas',
         date(2024, 3, 15), date(2024, 3, 22), '11204', 'oceanview', '12', 1499.0, 4,
         'Great Bahamas getaway. The aqua park onboard was a highlight.'),
        (demo, 'Carnival Cruise Line', 'Carnival Celebration', 'Caribbean',
         date(2024, 9, 7), date(2024, 9, 14), '6C', 'balcony', '7', 1799.0, 4,
         'Loved the new ship. Lots of dining options and activities.'),
        # Second user's cruise
        (second, 'Celebrity Cruises', 'Celebrity Edge', 'Mediterranean',
         date(2024, 6, 1), date(2024, 6, 14), 'SS1022', 'suite', '14', 5499.0, 5,
         'Absolutely breathtaking. The Edge class ship is stunning.'),
    ]

    for user, line_name, ship_name, region_name, begin, end, cabin, cabin_type, deck, cost, rating, notes in cruise_data:
        c = CruiseHistory(
            user_id=user.id,
            cruiseline_id=lines[line_name].id,
            ship_id=ships[ship_name].id,
            region_id=regions[region_name].id,
            begindate=begin, enddate=end,
            cabin_number=cabin, cabin_type=cabin_type, deck=deck,
            cost=cost, rating=rating, notes=notes,
        )
        db.session.add(c)
        cruises.append(c)

    db.session.flush()
    db.session.commit()
    print(f'Seeded {len(cruises)} cruise histories.')
    return cruises


def seed_cruise_ports(cruises, ports):
    itineraries = {
        0: [  # Symphony of the Seas Caribbean
            ('Port of Miami', date(2023, 12, 9), 1),
            ('Nassau Cruise Port', date(2023, 12, 11), 2),
            ('Cozumel Pier', date(2023, 12, 13), 3),
            ('Port of Miami', date(2023, 12, 16), 4),
        ],
        1: [  # Norwegian Escape Bahamas
            ('Port Canaveral', date(2024, 3, 15), 1),
            ('Nassau Cruise Port', date(2024, 3, 17), 2),
            ('Port Canaveral', date(2024, 3, 22), 3),
        ],
        3: [  # Celebrity Edge Mediterranean
            ('Barcelona Cruise Port', date(2024, 6, 1), 1),
            ('Civitavecchia Port', date(2024, 6, 4), 2),
            ('Venice Cruise Terminal', date(2024, 6, 8), 3),
            ('Barcelona Cruise Port', date(2024, 6, 14), 4),
        ],
    }

    for idx, stops in itineraries.items():
        cruise = cruises[idx]
        for port_name, visit_date, order in stops:
            if port_name in ports:
                cp = CruisePort(cruise_id=cruise.cruiseid,
                                port_id=ports[port_name].id,
                                visit_order=order, visit_date=visit_date)
                db.session.add(cp)

    db.session.commit()
    print('Seeded cruise port itineraries.')


def seed_social(demo, second, cruises):
    # Social profiles
    demo_profile = SocialProfile.query.filter_by(user_id=demo.id).first()
    if not demo_profile:
        demo_profile = SocialProfile(
            user_id=demo.id,
            display_name='Joshua — Cruise Explorer',
            bio='Avid cruiser tracking every voyage. 3 cruises and counting! '
                'Caribbean specialist, always chasing the next horizon. ⚓',
            hometown='Miami, FL',
            sailing_status='planning',
        )
        db.session.add(demo_profile)

    second_profile = SocialProfile.query.filter_by(user_id=second.id).first()
    if not second_profile:
        second_profile = SocialProfile(
            user_id=second.id,
            display_name='Ocean Wanderer',
            bio='Mediterranean obsessed. I let the sea decide where I go next. 🌊',
            hometown='Tampa, FL',
        )
        db.session.add(second_profile)

    db.session.flush()

    # Follow relationship
    follow = UserFollow.query.filter_by(follower_id=demo.id, following_id=second.id).first()
    if not follow:
        db.session.add(UserFollow(follower_id=demo.id, following_id=second.id))
    follow2 = UserFollow.query.filter_by(follower_id=second.id, following_id=demo.id).first()
    if not follow2:
        db.session.add(UserFollow(follower_id=second.id, following_id=demo.id))

    # Posts
    if SocialPost.query.filter_by(user_id=demo.id).count() == 0:
        posts_data = [
            (demo, cruises[0].cruiseid,
             "Just got back from Symphony of the Seas — absolutely incredible! "
             "7 nights in the Caribbean and I'm already planning the next one. "
             "The FlowRider surf simulator was a highlight 🏄‍♂️",
             'Port of Miami, FL', '#RoyalCaribbean #Caribbean #CruiseLife'),
            (demo, cruises[1].cruiseid,
             "Bahamas trip on Norwegian Escape was perfect. Nassau is always a vibe. "
             "Highly recommend the Aqua Park — best at sea! 🌊",
             'Nassau, Bahamas', '#Norwegian #Bahamas #CruiseLife'),
            (second, cruises[3].cruiseid,
             "Mediterranean on Celebrity Edge was on another level. "
             "Barcelona to Venice in 14 days — this is the way to see Europe. "
             "The Rooftop Garden is unreal 🌿",
             'Barcelona, Spain', '#CelebrityEdge #Mediterranean #LuxuryCruise'),
        ]

        for user, cruise_id, content, location, hashtags in posts_data:
            post = SocialPost(
                user_id=user.id,
                content=content,
                shared_cruise_id=cruise_id,
                location=location,
                hashtags=hashtags,
                created_at=datetime.utcnow(),
            )
            db.session.add(post)

        db.session.flush()

        # Likes and comments
        all_posts = SocialPost.query.all()
        for post in all_posts:
            liker = second if post.user_id == demo.id else demo
            if not PostLike.query.filter_by(post_id=post.id, user_id=liker.id).first():
                db.session.add(PostLike(post_id=post.id, user_id=liker.id))

        first_post = SocialPost.query.filter_by(user_id=demo.id).order_by(SocialPost.created_at).first()
        if first_post and PostComment.query.filter_by(post_id=first_post.id).count() == 0:
            db.session.add(PostComment(
                post_id=first_post.id, user_id=second.id,
                content='Symphony is on my bucket list! How was the dining?'
            ))

    db.session.commit()
    print('Social profiles, posts, likes, and comments seeded.')


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    with app.app_context():
        demo_exists = User.query.filter_by(email='demo@histacruise.com').first()
        if demo_exists:
            print('Demo user already exists — skipping to avoid duplicates.')
            print('To reseed, delete the database and run again.')
            return

        print('Seeding Histacruise database...')
        lines, ships, regions, ports = seed_reference_data()
        demo, second                 = seed_users()
        cruises                      = seed_cruises(demo, second, lines, ships, regions)
        seed_cruise_ports(cruises, ports)
        seed_social(demo, second, cruises)

        print('\nHistacruise seeding complete.')
        print('-' * 40)
        print('Demo login:')
        print('  Email:    demo@histacruise.com')
        print('  Password: Demo1234!')


if __name__ == '__main__':
    main()
