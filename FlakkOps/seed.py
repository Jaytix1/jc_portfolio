"""
FlakkOps Seed Script
====================
Populates the database with realistic demo data for portfolio demonstrations.

Usage:
    python seed.py

Safe to run multiple times — clears existing data first.
"""

from models import init_db, get_db
from datetime import datetime, date, timedelta
import os

DATABASE = 'flakkops.db'


def clear_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM manifest_items')
    cur.execute('DELETE FROM tasks')
    cur.execute('DELETE FROM manifests')
    cur.execute('DELETE FROM products')
    cur.execute('DELETE FROM weekly_history')
    # Reset autoincrement counters
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('manifests','products','manifest_items','tasks','weekly_history')")
    conn.commit()
    conn.close()
    print('Cleared existing data.')


def seed_products(conn):
    cur = conn.cursor()
    products = [
        ('SK-8750-BLK', 'Arch Fit - Slip Resistant Work', 'Work'),
        ('SK-8751-NVY', 'Arch Fit - Slip Resistant Work Navy', 'Work'),
        ('SK-2330-WHT', 'Summits - Fast Attraction', 'Athletic'),
        ('SK-2331-GRY', 'Summits - Fast Attraction Grey', 'Athletic'),
        ('SK-4040-PNK', 'D\'Lites - Fresh Start Pink', 'Lifestyle'),
        ('SK-4041-PRP', 'D\'Lites - Fresh Start Purple', 'Lifestyle'),
        ('SK-6600-TAN', 'Relaxed Fit - Expected Avillo', 'Comfort'),
        ('SK-6601-BRN', 'Relaxed Fit - Expected Avillo Brown', 'Comfort'),
        ('SK-9010-BLK', 'GO Run Consistent - Ridgeback', 'Running'),
        ('SK-9011-BLU', 'GO Run Consistent - Ridgeback Blue', 'Running'),
        ('SK-1200-MUL', 'Flex Appeal 4.0 - Brilliant View', 'Athletic'),
        ('SK-5500-GRN', 'Max Cushioning Premier', 'Running'),
        ('SK-3300-RED', 'Sport - Stamina Nuovo Red', 'Sport'),
        ('SK-SPNG-WHT', 'Spring Stride Pro White', 'Running'),
        ('SK-SPNG-BLU', 'Spring Stride Pro Blue', 'Running'),
    ]
    for sku, name, category in products:
        cur.execute('''
            INSERT OR IGNORE INTO products (sku, name, category, is_new)
            VALUES (?, ?, ?, 0)
        ''', (sku, name, category))
    conn.commit()
    print(f'Seeded {len(products)} products.')
    return {row[0]: row for row in products}


def seed_manifests(conn):
    cur = conn.cursor()
    today = date.today()

    manifests = [
        # --- Older processed manifests (4-7 weeks ago) ---
        {
            'filename': 'manifest_2026_01_12.pdf',
            'manifest_date': (today - timedelta(weeks=7)).strftime('%Y-%m-%d'),
            'arrival_date': (today - timedelta(weeks=7, days=-1)).strftime('%Y-%m-%d'),
            'arrival_day': 'Monday',
            'total_skus': 7,
            'total_units': 290,
            'processed': 1,
            'notes': 'Regular Monday replenishment. High volume on work SKUs.',
        },
        {
            'filename': 'manifest_2026_01_14.pdf',
            'manifest_date': (today - timedelta(weeks=6, days=5)).strftime('%Y-%m-%d'),
            'arrival_date': (today - timedelta(weeks=6, days=3)).strftime('%Y-%m-%d'),
            'arrival_day': 'Wednesday',
            'total_skus': 5,
            'total_units': 178,
            'processed': 1,
            'notes': 'Mid-week top-up. Athletic and running lines.',
        },
        {
            'filename': 'manifest_2026_01_19.pdf',
            'manifest_date': (today - timedelta(weeks=6)).strftime('%Y-%m-%d'),
            'arrival_date': (today - timedelta(weeks=6, days=-1)).strftime('%Y-%m-%d'),
            'arrival_day': 'Monday',
            'total_skus': 8,
            'total_units': 325,
            'processed': 1,
            'notes': 'Large Monday truck. Pre-season stock build.',
        },
        {
            'filename': 'manifest_2026_01_21.pdf',
            'manifest_date': (today - timedelta(weeks=5, days=5)).strftime('%Y-%m-%d'),
            'arrival_date': (today - timedelta(weeks=5, days=3)).strftime('%Y-%m-%d'),
            'arrival_day': 'Wednesday',
            'total_skus': 6,
            'total_units': 215,
            'processed': 1,
            'notes': 'Comfort and lifestyle lines restocked.',
        },
        {
            'filename': 'manifest_2026_01_26.pdf',
            'manifest_date': (today - timedelta(weeks=5)).strftime('%Y-%m-%d'),
            'arrival_date': (today - timedelta(weeks=5, days=-1)).strftime('%Y-%m-%d'),
            'arrival_day': 'Monday',
            'total_skus': 7,
            'total_units': 268,
            'processed': 1,
            'notes': 'Standard weekly. 1 overcount flagged and corrected.',
        },
        # --- Recent processed manifests ---
        {
            'filename': 'manifest_2026_02_17.pdf',
            'manifest_date': (today - timedelta(days=21)).strftime('%Y-%m-%d'),
            'arrival_date': (today - timedelta(days=14)).strftime('%Y-%m-%d'),
            'arrival_day': 'Monday',
            'total_skus': 8,
            'total_units': 312,
            'processed': 1,
            'notes': 'Standard weekly replenishment. All items received and processed.',
        },
        {
            'filename': 'manifest_2026_02_24.pdf',
            'manifest_date': (today - timedelta(days=14)).strftime('%Y-%m-%d'),
            'arrival_date': (today - timedelta(days=7)).strftime('%Y-%m-%d'),
            'arrival_day': 'Wednesday',
            'total_skus': 6,
            'total_units': 204,
            'processed': 1,
            'notes': 'Mid-week shipment. 2 new SKUs flagged for review.',
        },
        # --- Upcoming manifests ---
        {
            'filename': 'manifest_2026_03_03.pdf',
            'manifest_date': today.strftime('%Y-%m-%d'),
            'arrival_date': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
            'arrival_day': 'Monday',
            'total_skus': 8,
            'total_units': 330,
            'processed': 0,
            'notes': 'Pending processing. Spring collection items expected.',
        },
        {
            'filename': 'manifest_2026_03_05.pdf',
            'manifest_date': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            'arrival_date': (today + timedelta(days=5)).strftime('%Y-%m-%d'),
            'arrival_day': 'Wednesday',
            'total_skus': 5,
            'total_units': 192,
            'processed': 0,
            'notes': 'Wednesday mid-week fill-in. Running and athletic replenishment.',
        },
    ]

    ids = []
    for m in manifests:
        cur.execute('''
            INSERT INTO manifests
                (filename, manifest_date, arrival_date, arrival_day, total_skus, total_units, processed, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (m['filename'], m['manifest_date'], m['arrival_date'], m['arrival_day'],
              m['total_skus'], m['total_units'], m['processed'], m['notes']))
        ids.append(cur.lastrowid)
    conn.commit()
    print(f'Seeded {len(manifests)} manifests.')
    return ids


def _insert_items(cur, manifest_id, items, new_skus=None):
    """Helper: insert a list of (sku, desc, qty, case_pack, weight) into manifest_items."""
    new_skus = new_skus or set()
    for sku, desc, qty, case_pack, weight in items:
        cur.execute('SELECT id FROM products WHERE sku = ?', (sku,))
        row = cur.fetchone()
        product_id = row[0] if row else None
        cur.execute('''
            INSERT INTO manifest_items (manifest_id, product_id, sku, description, quantity, case_pack, weight, is_new_product)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (manifest_id, product_id, sku, desc, qty, case_pack, weight, 1 if sku in new_skus else 0))


def seed_manifest_items(conn, manifest_ids):
    cur = conn.cursor()

    # manifest_ids layout:
    # [0] 7 wks ago Mon  [1] 6 wks Wed  [2] 6 wks Mon  [3] 5 wks Wed
    # [4] 5 wks Mon      [5] 3 wks Mon  [6] 1 wk Wed
    # [7] upcoming Mon   [8] upcoming Wed

    _insert_items(cur, manifest_ids[0], [
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    42, 6,  18.2),
        ('SK-8751-NVY', 'Arch Fit Slip Resistant - Navy',     36, 6,  18.2),
        ('SK-9010-BLK', 'GO Run Consistent - Black',          36, 6,  13.1),
        ('SK-6600-TAN', 'Relaxed Fit Expected Avillo - Tan',  48, 6,  19.5),
        ('SK-2330-WHT', 'Summits Fast Attraction - White',    54, 12, 12.4),
        ('SK-4040-PNK', "D'Lites Fresh Start - Pink",         30, 6,  16.8),
        ('SK-5500-GRN', 'Max Cushioning Premier - Green',     24, 6,  14.6),
    ])

    _insert_items(cur, manifest_ids[1], [
        ('SK-2331-GRY', 'Summits Fast Attraction - Grey',     36, 12, 12.4),
        ('SK-9011-BLU', 'GO Run Consistent - Blue',           30, 6,  13.1),
        ('SK-4041-PRP', "D'Lites Fresh Start - Purple",       24, 6,  16.8),
        ('SK-5500-GRN', 'Max Cushioning Premier - Green',     48, 6,  14.6),
        ('SK-6601-BRN', 'Relaxed Fit Expected Avillo - Brown',40, 6,  19.5),
    ])

    _insert_items(cur, manifest_ids[2], [
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    48, 6,  18.2),
        ('SK-8751-NVY', 'Arch Fit Slip Resistant - Navy',     42, 6,  18.2),
        ('SK-2330-WHT', 'Summits Fast Attraction - White',    60, 12, 12.4),
        ('SK-2331-GRY', 'Summits Fast Attraction - Grey',     48, 12, 12.4),
        ('SK-4040-PNK', "D'Lites Fresh Start - Pink",         42, 6,  16.8),
        ('SK-6600-TAN', 'Relaxed Fit Expected Avillo - Tan',  36, 6,  19.5),
        ('SK-9010-BLK', 'GO Run Consistent - Black',          30, 6,  13.1),
        ('SK-5500-GRN', 'Max Cushioning Premier - Green',     19, 6,  14.6),
    ])

    _insert_items(cur, manifest_ids[3], [
        ('SK-4041-PRP', "D'Lites Fresh Start - Purple",       36, 6,  16.8),
        ('SK-6601-BRN', 'Relaxed Fit Expected Avillo - Brown',30, 6,  19.5),
        ('SK-9011-BLU', 'GO Run Consistent - Blue',           42, 6,  13.1),
        ('SK-1200-MUL', 'Flex Appeal 4.0 Brilliant View',     60, 12, 11.2),
        ('SK-3300-RED', 'Sport Stamina Nuovo - Red',          30, 6,  15.0),
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    17, 6,  18.2),
    ])

    _insert_items(cur, manifest_ids[4], [
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    36, 6,  18.2),
        ('SK-2330-WHT', 'Summits Fast Attraction - White',    48, 12, 12.4),
        ('SK-9010-BLK', 'GO Run Consistent - Black',          42, 6,  13.1),
        ('SK-6600-TAN', 'Relaxed Fit Expected Avillo - Tan',  30, 6,  19.5),
        ('SK-4040-PNK', "D'Lites Fresh Start - Pink",         36, 6,  16.8),
        ('SK-5500-GRN', 'Max Cushioning Premier - Green',     36, 6,  14.6),
        ('SK-1200-MUL', 'Flex Appeal 4.0 Brilliant View',     40, 12, 11.2),
    ])

    # manifest [5]: 3 wks ago Monday (was manifest_ids[0])
    _insert_items(cur, manifest_ids[5], [
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    48, 6,  18.2),
        ('SK-8751-NVY', 'Arch Fit Slip Resistant - Navy',     36, 6,  18.2),
        ('SK-2330-WHT', 'Summits Fast Attraction - White',    60, 12, 12.4),
        ('SK-2331-GRY', 'Summits Fast Attraction - Grey',     48, 12, 12.4),
        ('SK-4040-PNK', "D'Lites Fresh Start - Pink",         36, 6,  16.8),
        ('SK-6600-TAN', 'Relaxed Fit Expected Avillo - Tan',  42, 6,  19.5),
        ('SK-9010-BLK', 'GO Run Consistent - Black',          24, 6,  13.1),
        ('SK-5500-GRN', 'Max Cushioning Premier - Green',     18, 6,  14.6),
    ])

    # manifest [6]: 1 wk ago Wednesday (was manifest_ids[1])
    _insert_items(cur, manifest_ids[6], [
        ('SK-4041-PRP', "D'Lites Fresh Start - Purple",       30, 6,  16.8),
        ('SK-6601-BRN', 'Relaxed Fit Expected Avillo - Brown',24, 6,  19.5),
        ('SK-9011-BLU', 'GO Run Consistent - Blue',           36, 6,  13.1),
        ('SK-1200-MUL', 'Flex Appeal 4.0 Brilliant View',     48, 12, 11.2),
        ('SK-3300-RED', 'Sport Stamina Nuovo - Red',          42, 6,  15.0),
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    24, 6,  18.2),
    ], new_skus={'SK-3300-RED', 'SK-1200-MUL'})

    # manifest [7]: upcoming Monday — spring collection
    _insert_items(cur, manifest_ids[7], [
        ('SK-5500-GRN', 'Max Cushioning Premier - Green',     36, 6,  14.6),
        ('SK-9010-BLK', 'GO Run Consistent - Black',          48, 6,  13.1),
        ('SK-2330-WHT', 'Summits Fast Attraction - White',    60, 12, 12.4),
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    36, 6,  18.2),
        ('SK-4040-PNK', "D'Lites Fresh Start - Pink",         24, 6,  16.8),
        ('SK-6600-TAN', 'Relaxed Fit Expected Avillo - Tan',  30, 6,  19.5),
        ('SK-SPNG-WHT', 'Spring Stride Pro - White',          48, 12, 11.8),
        ('SK-SPNG-BLU', 'Spring Stride Pro - Blue',           48, 12, 11.8),
    ], new_skus={'SK-SPNG-WHT', 'SK-SPNG-BLU'})

    # manifest [8]: upcoming Wednesday — running/athletic fill-in
    _insert_items(cur, manifest_ids[8], [
        ('SK-9010-BLK', 'GO Run Consistent - Black',          36, 6,  13.1),
        ('SK-9011-BLU', 'GO Run Consistent - Blue',           36, 6,  13.1),
        ('SK-2330-WHT', 'Summits Fast Attraction - White',    48, 12, 12.4),
        ('SK-5500-GRN', 'Max Cushioning Premier - Green',     36, 6,  14.6),
        ('SK-1200-MUL', 'Flex Appeal 4.0 Brilliant View',     36, 12, 11.2),
    ])

    conn.commit()
    print('Seeded manifest items.')


def seed_tasks(conn, manifest_ids):
    cur = conn.cursor()
    today = date.today()

    # Indices: [7]=upcoming Mon, [8]=upcoming Wed, [6]=last processed Wed, [5]=processed Mon
    tasks = [
        (manifest_ids[7], 'Receive Monday truck shipment',
         'Unload and verify all items against manifest_2026_03_03.pdf. Check for damage.',
         'high', 'pending', (today + timedelta(days=3)).strftime('%Y-%m-%d')),
        (manifest_ids[7], 'Update inventory counts post-arrival',
         'Enter received quantities into inventory system and flag discrepancies.',
         'high', 'pending', (today + timedelta(days=4)).strftime('%Y-%m-%d')),
        (manifest_ids[7], 'Review spring collection new SKUs',
         'Check new Spring 2026 SKUs against product catalog and set up display locations.',
         'medium', 'pending', (today + timedelta(days=5)).strftime('%Y-%m-%d')),
        (manifest_ids[8], 'Prepare for Wednesday mid-week truck',
         'Clear floor space and stage receiving area for running/athletic replenishment.',
         'medium', 'pending', (today + timedelta(days=5)).strftime('%Y-%m-%d')),
        (manifest_ids[6], 'Mark new SKUs from last shipment',
         'Flag SK-3300-RED and SK-1200-MUL as reviewed after floor placement.',
         'low', 'in_progress', (today + timedelta(days=1)).strftime('%Y-%m-%d')),
        (manifest_ids[5], 'Archive February manifests',
         'Move processed February manifests to archive folder and update records.',
         'low', 'completed', (today - timedelta(days=7)).strftime('%Y-%m-%d')),
    ]

    for manifest_id, title, desc, priority, status, due_date in tasks:
        completed_at = datetime.utcnow().isoformat() if status == 'completed' else None
        cur.execute('''
            INSERT INTO tasks (manifest_id, title, description, priority, status, due_date, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (manifest_id, title, desc, priority, status, due_date, completed_at))

    conn.commit()
    print(f'Seeded {len(tasks)} tasks.')


def seed_weekly_history(conn):
    cur = conn.cursor()
    today = date.today()

    # Varied values: oldest → newest (i=0 oldest, i=7 most recent)
    units_2026 = [220, 280, 310, 265, 295, 345, 270, 320]
    units_2025 = [185, 248, 275, 230, 265, 305, 242, 288]
    skus_2026  = [6, 7, 8, 7, 7, 8, 7, 8]
    skus_2025  = [5, 6, 7, 6, 6, 7, 6, 7]

    history = []
    for i, weeks_ago in enumerate(range(8, 0, -1)):
        ref_date = today - timedelta(weeks=weeks_ago)
        week_num = ref_date.isocalendar()[1]
        history.append((2026, week_num, skus_2026[i], units_2026[i], '["SK-8750-BLK","SK-2330-WHT","SK-4040-PNK"]'))
        history.append((2025, week_num, skus_2025[i], units_2025[i], '["SK-8750-BLK","SK-2330-WHT","SK-6600-TAN"]'))

    for year, week_num, skus, units, top_products in history:
        cur.execute('''
            INSERT OR IGNORE INTO weekly_history (year, week_number, total_skus, total_units, top_products)
            VALUES (?, ?, ?, ?, ?)
        ''', (year, week_num, skus, units, top_products))

    conn.commit()
    print(f'Seeded {len(history)} weekly history records.')


def main():
    if os.path.exists(DATABASE):
        print(f'Database found: {DATABASE}')
        clear_db()
    else:
        from models import init_db
        init_db()
        print(f'Created new database: {DATABASE}')

    conn = get_db()
    seed_products(conn)
    manifest_ids = seed_manifests(conn)
    seed_manifest_items(conn, manifest_ids)
    seed_tasks(conn, manifest_ids)
    seed_weekly_history(conn)
    conn.close()
    print('\nFlakkOps seeding complete.')


if __name__ == '__main__':
    main()
