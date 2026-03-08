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

CRUISE_LINES = [
    'Royal Caribbean', 'Carnival Cruise Line', 'Norwegian Cruise Line',
    'Celebrity Cruises', 'Disney Cruise Line', 'MSC Cruises',
    'Princess Cruises', 'Holland America Line', 'Costa Cruises',
    'AIDA Cruises', 'Virgin Voyages', 'Cunard', 'Oceania Cruises',
    'Azamara', 'Regent Seven Seas Cruises', 'Silversea Cruises',
    'Viking Ocean Cruises', 'Seabourn', 'P&O Cruises',
]

SHIPS = {
    'Royal Caribbean': [
        'Wonder of the Seas', 'Symphony of the Seas', 'Harmony of the Seas',
        'Allure of the Seas', 'Oasis of the Seas', 'Icon of the Seas',
        'Odyssey of the Seas', 'Quantum of the Seas', 'Anthem of the Seas',
        'Ovation of the Seas', 'Navigator of the Seas', 'Mariner of the Seas',
        'Explorer of the Seas', 'Adventure of the Seas', 'Freedom of the Seas',
        'Liberty of the Seas', 'Independence of the Seas', 'Brilliance of the Seas',
        'Serenade of the Seas', 'Jewel of the Seas', 'Enchantment of the Seas',
        'Vision of the Seas',
    ],
    'Carnival Cruise Line': [
        'Mardi Gras', 'Carnival Celebration', 'Carnival Jubilee',
        'Carnival Horizon', 'Carnival Vista', 'Carnival Panorama',
        'Carnival Sunshine', 'Carnival Sunrise', 'Carnival Magic',
        'Carnival Breeze', 'Carnival Dream', 'Carnival Freedom',
        'Carnival Liberty', 'Carnival Valor', 'Carnival Conquest',
        'Carnival Glory', 'Carnival Miracle', 'Carnival Legend',
        'Carnival Pride', 'Carnival Spirit', 'Carnival Elation',
        'Carnival Paradise',
    ],
    'Norwegian Cruise Line': [
        'Norwegian Prima', 'Norwegian Viva', 'Norwegian Escape',
        'Norwegian Bliss', 'Norwegian Encore', 'Norwegian Joy',
        'Norwegian Breakaway', 'Norwegian Getaway', 'Norwegian Epic',
        'Norwegian Pearl', 'Norwegian Jade', 'Norwegian Gem',
        'Norwegian Dawn', 'Norwegian Star', 'Norwegian Sun',
        'Norwegian Sky', 'Norwegian Spirit',
    ],
    'Celebrity Cruises': [
        'Celebrity Ascent', 'Celebrity Beyond', 'Celebrity Apex',
        'Celebrity Edge', 'Celebrity Reflection', 'Celebrity Silhouette',
        'Celebrity Equinox', 'Celebrity Eclipse', 'Celebrity Solstice',
        'Celebrity Constellation', 'Celebrity Summit', 'Celebrity Millennium',
        'Celebrity Infinity', 'Celebrity Xcel',
    ],
    'Disney Cruise Line': [
        'Disney Wish', 'Disney Dream', 'Disney Fantasy',
        'Disney Magic', 'Disney Wonder', 'Disney Treasure',
    ],
    'MSC Cruises': [
        'MSC World Europa', 'MSC Seashore', 'MSC Seascape',
        'MSC Virtuosa', 'MSC Grandiosa', 'MSC Bellissima',
        'MSC Meraviglia', 'MSC Seaview', 'MSC Seaside',
        'MSC Preziosa', 'MSC Divina', 'MSC Splendida',
        'MSC Fantasia', 'MSC Musica', 'MSC Orchestra',
    ],
    'Princess Cruises': [
        'Sun Princess', 'Star Princess', 'Discovery Princess',
        'Enchanted Princess', 'Sky Princess', 'Majestic Princess',
        'Regal Princess', 'Royal Princess', 'Caribbean Princess',
        'Crown Princess', 'Emerald Princess', 'Ruby Princess',
        'Sapphire Princess', 'Diamond Princess', 'Coral Princess',
        'Island Princess',
    ],
    'Holland America Line': [
        'Rotterdam', 'Nieuw Statendam', 'Koningsdam',
        'Oosterdam', 'Westerdam', 'Noordam',
        'Zuiderdam', 'Eurodam', 'Nieuw Amsterdam',
        'Volendam', 'Zaandam',
    ],
    'Costa Cruises': [
        'Costa Toscana', 'Costa Firenze', 'Costa Smeralda',
        'Costa Luminosa', 'Costa Deliziosa', 'Costa Fascinosa',
        'Costa Favolosa', 'Costa Diadema', 'Costa Pacifica',
        'Costa Serena', 'Costa Magica', 'Costa Fortuna',
    ],
    'AIDA Cruises': [
        'AIDAnova', 'AIDAcosma', 'AIDAprima', 'AIDAperla',
        'AIDAbella', 'AIDAluna', 'AIDAmar', 'AIDAstella',
        'AIDAsol', 'AIDAdiva', 'AIDAaura', 'AIDAvita',
    ],
    'Virgin Voyages': [
        'Scarlet Lady', 'Valiant Lady', 'Resilient Lady', 'Brilliant Lady',
    ],
    'Cunard': [
        'Queen Mary 2', 'Queen Victoria', 'Queen Elizabeth', 'Queen Anne',
    ],
    'Oceania Cruises': [
        'Vista', 'Riviera', 'Marina', 'Insignia',
        'Nautica', 'Regatta', 'Sirena',
    ],
    'Azamara': [
        'Azamara Quest', 'Azamara Journey', 'Azamara Pursuit',
        'Azamara Onward',
    ],
    'Regent Seven Seas Cruises': [
        'Seven Seas Grandeur', 'Seven Seas Splendor', 'Seven Seas Explorer',
        'Seven Seas Voyager', 'Seven Seas Navigator', 'Seven Seas Mariner',
    ],
    'Silversea Cruises': [
        'Silver Nova', 'Silver Dawn', 'Silver Moon', 'Silver Origin',
        'Silver Muse', 'Silver Spirit', 'Silver Shadow', 'Silver Whisper',
        'Silver Wind', 'Silver Cloud',
    ],
    'Viking Ocean Cruises': [
        'Viking Jupiter', 'Viking Saturn', 'Viking Neptune', 'Viking Mars',
        'Viking Venus', 'Viking Orion', 'Viking Sky', 'Viking Sea',
        'Viking Star',
    ],
    'Seabourn': [
        'Seabourn Pursuit', 'Seabourn Venture', 'Seabourn Encore',
        'Seabourn Ovation', 'Seabourn Odyssey', 'Seabourn Sojourn',
        'Seabourn Quest',
    ],
    'P&O Cruises': [
        'Iona', 'Arvia', 'Britannia', 'Aurora', 'Arcadia', 'Ventura', 'Azura',
    ],
}

REGIONS = [
    'Caribbean', 'Mediterranean', 'Alaska', 'Bahamas',
    'Northern Europe', 'Mexico', 'Hawaii', 'Bermuda',
    'South America', 'Asia', 'Australia & New Zealand',
    'Transatlantic', 'Canary Islands', 'British Isles',
    'Indian Ocean', 'Middle East', 'Africa',
]

PORTS = [
    # ── United States ──────────────────────────────────────────────────────
    ('Port of Miami',              'Miami',           'United States',  25.7742,  -80.1747),
    ('Port Everglades',            'Fort Lauderdale', 'United States',  26.0979,  -80.1150),
    ('Port Canaveral',             'Cape Canaveral',  'United States',  28.4158,  -80.5917),
    ('Port of Tampa',              'Tampa',           'United States',  27.9290,  -82.4459),
    ('Port of New Orleans',        'New Orleans',     'United States',  29.9457,  -90.0615),
    ('Port of Galveston',          'Galveston',       'United States',  29.3013,  -94.7977),
    ('Port of Baltimore',          'Baltimore',       'United States',  39.2604,  -76.5788),
    ('Port of New York',           'New York',        'United States',  40.6892,  -74.0445),
    ('Port of Seattle',            'Seattle',         'United States',  47.6062, -122.3321),
    ('Port of San Francisco',      'San Francisco',   'United States',  37.8044, -122.4730),
    ('Port of Los Angeles',        'Los Angeles',     'United States',  33.7394, -118.2630),
    ('Port of San Diego',          'San Diego',       'United States',  32.7157, -117.1611),
    ('Juneau Cruise Terminal',     'Juneau',          'United States',  58.3005, -134.4197),
    ('Skagway Cruise Terminal',    'Skagway',         'United States',  59.4583, -135.3139),
    ('Ketchikan Cruise Terminal',  'Ketchikan',       'United States',  55.3422, -131.6461),
    ('Sitka Cruise Terminal',      'Sitka',           'United States',  57.0531, -135.3300),
    ('Seward Cruise Terminal',     'Seward',          'United States',  60.1041, -149.4428),
    ('Whittier Cruise Terminal',   'Whittier',        'United States',  60.7738, -148.6838),
    # ── Bahamas ────────────────────────────────────────────────────────────
    ('Nassau Cruise Port',         'Nassau',          'Bahamas',        25.0833,  -77.3500),
    ('Freeport Cruise Port',       'Freeport',        'Bahamas',        26.5285,  -78.6956),
    ('Perfect Day at CocoCay',     'CocoCay',         'Bahamas',        25.8233,  -77.8308),
    ('Half Moon Cay',              'Half Moon Cay',   'Bahamas',        25.0658,  -77.3825),
    ('Princess Cays',              'Eleuthera',       'Bahamas',        25.1280,  -76.1490),
    # ── Mexico ─────────────────────────────────────────────────────────────
    ('Cozumel Pier',               'Cozumel',         'Mexico',         20.5088,  -86.9517),
    ('Ensenada Cruise Terminal',   'Ensenada',        'Mexico',         31.8676, -116.5961),
    ('Puerto Vallarta',            'Puerto Vallarta',  'Mexico',        20.6534, -105.2253),
    ('Cabo San Lucas',             'Cabo San Lucas',  'Mexico',         22.8905, -109.9167),
    ('Mazatlan',                   'Mazatlan',        'Mexico',         23.2494, -106.4111),
    ('Manzanillo',                 'Manzanillo',      'Mexico',         19.0522, -104.3190),
    ('Costa Maya',                 'Mahahual',        'Mexico',         18.7130,  -87.7040),
    ('Progreso',                   'Progreso',        'Mexico',         21.2833,  -89.6667),
    # ── Caribbean (Islands) ────────────────────────────────────────────────
    ('St. Thomas WICO',            'Charlotte Amalie','US Virgin Islands',18.3381,-64.9307),
    ('Frederiksted Pier',          'Frederiksted',    'US Virgin Islands',17.7133,-64.8811),
    ('San Juan Cruise Terminal',   'San Juan',        'Puerto Rico',    18.4655,  -66.1057),
    ('Grand Cayman Cruise Terminal','George Town',    'Cayman Islands', 19.2869,  -81.3674),
    ('Falmouth Cruise Terminal',   'Falmouth',        'Jamaica',        18.4942,  -77.6560),
    ('Ocho Rios Cruise Terminal',  'Ocho Rios',       'Jamaica',        18.4082,  -77.1040),
    ('Montego Bay Cruise Port',    'Montego Bay',     'Jamaica',        18.4678,  -77.9128),
    ('Philipsburg Cruise Terminal','Philipsburg',     'Sint Maarten',   18.0278,  -63.0444),
    ('Oranjestad Cruise Port',     'Oranjestad',      'Aruba',          12.5246,  -70.0273),
    ('Willemstad Cruise Terminal', 'Willemstad',      'Curacao',        12.1084,  -68.9335),
    ('Bridgetown Cruise Terminal', 'Bridgetown',      'Barbados',       13.1132,  -59.6199),
    ('Castries Cruise Terminal',   'Castries',        'St. Lucia',      14.0101,  -60.9872),
    ('Basseterre Cruise Port',     'Basseterre',      'St. Kitts',      17.2983,  -62.7271),
    ('Roseau Cruise Terminal',     'Roseau',          'Dominica',       15.3017,  -61.3878),
    ('Gustavia Cruise Terminal',   'Gustavia',        'St. Barthelemy', 17.8964,  -62.8520),
    ('Pointe-a-Pitre',             'Pointe-a-Pitre',  'Guadeloupe',     16.2350,  -61.5344),
    ('Fort-de-France',             'Fort-de-France',  'Martinique',     14.6037,  -61.0735),
    ('Belize City Cruise Terminal','Belize City',     'Belize',         17.2510,  -88.7590),
    ('Roatan Cruise Terminal',     'Coxen Hole',      'Honduras',       16.3178,  -86.5358),
    ('Puerto Cortes',              'Puerto Cortes',   'Honduras',       15.8500,  -87.9333),
    # ── Bermuda ────────────────────────────────────────────────────────────
    ('Kings Wharf',                'Sandys Parish',   'Bermuda',        32.3078,  -64.8290),
    # ── Canada ─────────────────────────────────────────────────────────────
    ('Port of Vancouver',          'Vancouver',       'Canada',         49.2827, -123.1207),
    ('Port of Quebec',             'Quebec City',     'Canada',         46.8139,  -71.2080),
    ('Halifax Cruise Terminal',    'Halifax',         'Canada',         44.6488,  -63.5752),
    # ── Hawaii ─────────────────────────────────────────────────────────────
    ('Honolulu Cruise Terminal',   'Honolulu',        'United States',  21.3069, -157.8583),
    ('Kahului Harbor',             'Kahului',         'United States',  20.8893, -156.4729),
    ('Nawiliwili Harbor',          'Lihue',           'United States',  21.9511, -159.3556),
    ('Hilo Harbor',                'Hilo',            'United States',  19.7297, -155.0900),
    # ── Mediterranean ──────────────────────────────────────────────────────
    ('Barcelona Cruise Port',      'Barcelona',       'Spain',          41.3614,    2.1731),
    ('Valencia Cruise Terminal',   'Valencia',        'Spain',          39.4699,   -0.3774),
    ('Malaga Cruise Port',         'Malaga',          'Spain',          36.7213,   -4.4214),
    ('Palma de Mallorca Port',     'Palma',           'Spain',          39.5696,    2.6502),
    ('Cadiz Cruise Terminal',      'Cadiz',           'Spain',          36.5271,   -6.2886),
    ('Civitavecchia Port',         'Rome',            'Italy',          42.0941,   11.7962),
    ('Venice Cruise Terminal',     'Venice',          'Italy',          45.4408,   12.3155),
    ('Naples Cruise Terminal',     'Naples',          'Italy',          40.8358,   14.2488),
    ('Livorno Cruise Terminal',    'Livorno',         'Italy',          43.5481,   10.3116),
    ('Genoa Cruise Terminal',      'Genoa',           'Italy',          44.4056,    8.9463),
    ('Messina Cruise Terminal',    'Messina',         'Italy',          38.1938,   15.5540),
    ('Palermo Cruise Terminal',    'Palermo',         'Italy',          38.1157,   13.3615),
    ('Cagliari Cruise Terminal',   'Cagliari',        'Italy',          39.2238,    9.1217),
    ('Marseille Cruise Terminal',  'Marseille',       'France',         43.2965,    5.3698),
    ('Monaco Cruise Terminal',     'Monaco',          'Monaco',         43.7384,    7.4246),
    ('Cannes Cruise Anchorage',    'Cannes',          'France',         43.5528,    7.0174),
    ('Piraeus Cruise Terminal',    'Athens',          'Greece',         37.9480,   23.6441),
    ('Santorini Cruise Anchorage', 'Fira',            'Greece',         36.4167,   25.4333),
    ('Mykonos Cruise Anchorage',   'Mykonos Town',    'Greece',         37.4467,   25.3289),
    ('Heraklion Cruise Port',      'Heraklion',       'Greece',         35.3387,   25.1442),
    ('Rhodes Cruise Terminal',     'Rhodes',          'Greece',         36.4349,   28.2176),
    ('Corfu Cruise Terminal',      'Corfu',           'Greece',         39.6243,   19.9217),
    ('Kotor Cruise Port',          'Kotor',           'Montenegro',     42.4247,   18.7712),
    ('Dubrovnik Cruise Port',      'Dubrovnik',       'Croatia',        42.6507,   18.0944),
    ('Split Cruise Terminal',      'Split',           'Croatia',        43.5081,   16.4402),
    ('Valletta Cruise Port',       'Valletta',        'Malta',          35.9042,   14.5189),
    ('Istanbul Cruise Terminal',   'Istanbul',        'Turkey',         41.0082,   28.9784),
    ('Kusadasi Cruise Port',       'Kusadasi',        'Turkey',         37.8586,   27.2594),
    ('Lisbon Cruise Terminal',     'Lisbon',          'Portugal',       38.7223,   -9.1393),
    ('Gibraltar Cruise Terminal',  'Gibraltar',       'Gibraltar',      36.1408,   -5.3536),
    # ── Northern Europe ────────────────────────────────────────────────────
    ('Southampton Cruise Terminal','Southampton',     'United Kingdom', 50.9097,   -1.4044),
    ('Dover Cruise Terminal',      'Dover',           'United Kingdom', 51.1279,    1.3134),
    ('Edinburgh (Leith)',          'Edinburgh',       'United Kingdom', 55.9533,   -3.1883),
    ('Liverpool Cruise Terminal',  'Liverpool',       'United Kingdom', 53.4084,   -2.9916),
    ('Amsterdam Cruise Terminal',  'Amsterdam',       'Netherlands',    52.3676,    4.9041),
    ('Zeebrugge Cruise Port',      'Bruges',          'Belgium',        51.3333,    3.2000),
    ('Hamburg Cruise Terminal',    'Hamburg',         'Germany',        53.5753,    9.9675),
    ('Copenhagen Cruise Terminal', 'Copenhagen',      'Denmark',        55.6761,   12.5683),
    ('Stockholm Cruise Terminal',  'Stockholm',       'Sweden',         59.3293,   18.0686),
    ('Helsinki Cruise Terminal',   'Helsinki',        'Finland',        60.1699,   24.9384),
    ('Tallinn Cruise Terminal',    'Tallinn',         'Estonia',        59.4370,   24.7536),
    ('Riga Cruise Terminal',       'Riga',            'Latvia',         56.9460,   24.1059),
    ('Oslo Cruise Terminal',       'Oslo',            'Norway',         59.9139,   10.7522),
    ('Bergen Cruise Terminal',     'Bergen',          'Norway',         60.3913,    5.3221),
    ('Stavanger Cruise Terminal',  'Stavanger',       'Norway',         58.9700,    5.7331),
    ('Reykjavik Cruise Terminal',  'Reykjavik',       'Iceland',        64.1355,  -21.8954),
    ('St. Petersburg Cruise Terminal','St. Petersburg','Russia',        59.9343,   30.3351),
    # ── South America ──────────────────────────────────────────────────────
    ('Buenos Aires Cruise Terminal','Buenos Aires',   'Argentina',     -34.6037,  -58.3816),
    ('Montevideo Cruise Terminal', 'Montevideo',      'Uruguay',       -34.9011,  -56.1645),
    ('Rio de Janeiro Cruise Port', 'Rio de Janeiro',  'Brazil',        -22.9068,  -43.1729),
    ('Santos Cruise Terminal',     'Santos',          'Brazil',        -23.9608,  -46.3336),
    ('Cartagena Cruise Terminal',  'Cartagena',       'Colombia',        10.3910,  -75.4794),
    ('Colon Cruise Terminal',      'Colon',           'Panama',           9.3547,  -79.9006),
    ('Valparaiso Cruise Terminal', 'Valparaiso',      'Chile',          -33.0472,  -71.6127),
    # ── Asia ───────────────────────────────────────────────────────────────
    ('Singapore Cruise Centre',    'Singapore',       'Singapore',        1.2566,  103.8198),
    ('Yokohama Cruise Terminal',   'Yokohama',        'Japan',           35.4437,  139.6380),
    ('Kobe Cruise Terminal',       'Kobe',            'Japan',           34.6901,  135.1956),
    ('Osaka Cruise Terminal',      'Osaka',           'Japan',           34.6937,  135.5023),
    ('Nagasaki Cruise Terminal',   'Nagasaki',        'Japan',           32.7503,  129.8777),
    ('Hong Kong Cruise Terminal',  'Hong Kong',       'Hong Kong',       22.3193,  114.1694),
    ('Shanghai Cruise Terminal',   'Shanghai',        'China',           31.2304,  121.4737),
    ('Tianjin Cruise Terminal',    'Tianjin',         'China',           38.9973,  117.7383),
    ('Busan Cruise Terminal',      'Busan',           'South Korea',     35.1796,  129.0756),
    ('Laem Chabang Cruise Terminal','Bangkok',        'Thailand',        13.0827,  100.8807),
    ('Ho Chi Minh City Port',      'Ho Chi Minh City','Vietnam',         10.8231,  106.6297),
    ('Da Nang Cruise Terminal',    'Da Nang',         'Vietnam',         16.0544,  108.2022),
    ('Bali Cruise Terminal',       'Benoa',           'Indonesia',       -8.7500,  115.2167),
    # ── Australia & New Zealand ────────────────────────────────────────────
    ('Sydney Overseas Passenger Terminal','Sydney',   'Australia',      -33.8688,  151.2093),
    ('Melbourne Cruise Terminal',  'Melbourne',       'Australia',      -37.8136,  144.9631),
    ('Brisbane Cruise Terminal',   'Brisbane',        'Australia',      -27.4698,  153.0251),
    ('Fremantle Cruise Terminal',  'Fremantle',       'Australia',      -32.0569,  115.7439),
    ('Auckland Cruise Terminal',   'Auckland',        'New Zealand',    -36.8485,  174.7633),
    ('Wellington Cruise Terminal', 'Wellington',      'New Zealand',    -41.2865,  174.7762),
    # ── Canary Islands ─────────────────────────────────────────────────────
    ('Las Palmas Cruise Port',     'Las Palmas',      'Spain',           28.1248,  -15.4300),
    ('Santa Cruz de Tenerife',     'Santa Cruz',      'Spain',           28.4636,  -16.2518),
    ('Arrecife Cruise Port',       'Lanzarote',       'Spain',           28.9637,  -13.5481),
    # ── Middle East ────────────────────────────────────────────────────────
    ('Dubai Cruise Terminal',      'Dubai',           'UAE',             25.2048,   55.2708),
    ('Abu Dhabi Cruise Terminal',  'Abu Dhabi',       'UAE',             24.4539,   54.3773),
    ('Aqaba Cruise Terminal',      'Aqaba',           'Jordan',          29.5269,   35.0060),
    # ── Africa ─────────────────────────────────────────────────────────────
    ('Cape Town Cruise Terminal',  'Cape Town',       'South Africa',   -33.9249,   18.4241),
    ('Mombasa Cruise Terminal',    'Mombasa',         'Kenya',           -4.0435,   39.6682),
    ('Port Louis Cruise Terminal', 'Port Louis',      'Mauritius',      -20.1609,   57.4989),
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
        # Reference data always syncs — safe to run on existing DBs (uses get_or_create)
        print('Syncing reference data (cruise lines, ships, regions, ports)...')
        lines, ships, regions, ports = seed_reference_data()

        demo_exists = User.query.filter_by(email='demo@histacruise.com').first()
        if demo_exists:
            print('Demo user already exists — skipping user/social seed.')
            return

        print('Seeding Histacruise database...')
        demo, second = seed_users()
        cruises      = seed_cruises(demo, second, lines, ships, regions)
        seed_cruise_ports(cruises, ports)
        seed_social(demo, second, cruises)

        print('\nHistacruise seeding complete.')
        print('-' * 40)
        print('Demo login:')
        print('  Email:    demo@histacruise.com')
        print('  Password: Demo1234!')


if __name__ == '__main__':
    main()
