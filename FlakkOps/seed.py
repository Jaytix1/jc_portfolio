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
        # Past processed manifest
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
        # Recent processed manifest
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
        # Upcoming manifest
        {
            'filename': 'manifest_2026_03_03.pdf',
            'manifest_date': today.strftime('%Y-%m-%d'),
            'arrival_date': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
            'arrival_day': 'Monday',
            'total_skus': 0,
            'total_units': 0,
            'processed': 0,
            'notes': 'Pending processing. Spring collection items expected.',
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


def seed_manifest_items(conn, manifest_ids):
    cur = conn.cursor()

    # Items for manifest 1 (past, processed)
    m1_items = [
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    48, 6,  18.2),
        ('SK-8751-NVY', 'Arch Fit Slip Resistant - Navy',     36, 6,  18.2),
        ('SK-2330-WHT', 'Summits Fast Attraction - White',    60, 12, 12.4),
        ('SK-2331-GRY', 'Summits Fast Attraction - Grey',     48, 12, 12.4),
        ('SK-4040-PNK', "D'Lites Fresh Start - Pink",         36, 6,  16.8),
        ('SK-6600-TAN', 'Relaxed Fit Expected Avillo - Tan',  42, 6,  19.5),
        ('SK-9010-BLK', 'GO Run Consistent - Black',          24, 6,  13.1),
        ('SK-5500-GRN', 'Max Cushioning Premier - Green',     18, 6,  14.6),
    ]

    # Items for manifest 2 (recent, processed — includes 2 new products)
    m2_items = [
        ('SK-4041-PRP', "D'Lites Fresh Start - Purple",       30, 6,  16.8),
        ('SK-6601-BRN', 'Relaxed Fit Expected Avillo - Brown',24, 6,  19.5),
        ('SK-9011-BLU', 'GO Run Consistent - Blue',           36, 6,  13.1),
        ('SK-1200-MUL', 'Flex Appeal 4.0 Brilliant View',     48, 12, 11.2),
        ('SK-3300-RED', 'Sport Stamina Nuovo - Red',          42, 6,  15.0),
        ('SK-8750-BLK', 'Arch Fit Slip Resistant - Black',    24, 6,  18.2),
    ]

    for sku, desc, qty, case_pack, weight in m1_items:
        cur.execute('SELECT id FROM products WHERE sku = ?', (sku,))
        row = cur.fetchone()
        product_id = row[0] if row else None
        cur.execute('''
            INSERT INTO manifest_items (manifest_id, product_id, sku, description, quantity, case_pack, weight, is_new_product)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        ''', (manifest_ids[0], product_id, sku, desc, qty, case_pack, weight))

    new_skus = {'SK-3300-RED', 'SK-1200-MUL'}
    for sku, desc, qty, case_pack, weight in m2_items:
        cur.execute('SELECT id FROM products WHERE sku = ?', (sku,))
        row = cur.fetchone()
        product_id = row[0] if row else None
        is_new = 1 if sku in new_skus else 0
        cur.execute('''
            INSERT INTO manifest_items (manifest_id, product_id, sku, description, quantity, case_pack, weight, is_new_product)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (manifest_ids[1], product_id, sku, desc, qty, case_pack, weight, is_new))

    conn.commit()
    print('Seeded manifest items.')


def seed_tasks(conn, manifest_ids):
    cur = conn.cursor()
    today = date.today()

    tasks = [
        (manifest_ids[2], 'Receive Monday truck shipment',
         'Unload and verify all items against manifest_2026_03_03.pdf. Check for damage.',
         'high', 'pending', (today + timedelta(days=3)).strftime('%Y-%m-%d')),
        (manifest_ids[2], 'Update inventory counts post-arrival',
         'Enter received quantities into inventory system and flag discrepancies.',
         'high', 'pending', (today + timedelta(days=4)).strftime('%Y-%m-%d')),
        (manifest_ids[2], 'Review spring collection new SKUs',
         'Check new Spring 2026 SKUs against product catalog and set up display locations.',
         'medium', 'pending', (today + timedelta(days=5)).strftime('%Y-%m-%d')),
        (manifest_ids[1], 'Mark new SKUs from last shipment',
         'Flag SK-3300-RED and SK-1200-MUL as reviewed after floor placement.',
         'low', 'in_progress', (today + timedelta(days=1)).strftime('%Y-%m-%d')),
        (manifest_ids[0], 'Archive February manifests',
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

    # Seed 8 weeks of history for year-over-year comparison
    history = []
    for weeks_ago in range(1, 9):
        ref_date = today - timedelta(weeks=weeks_ago)
        week_num = ref_date.isocalendar()[1]
        # Current year
        history.append((2026, week_num, 7, 280, '["SK-8750-BLK","SK-2330-WHT","SK-4040-PNK"]'))
        # Previous year (same weeks)
        history.append((2025, week_num, 6, 245, '["SK-8750-BLK","SK-2330-WHT","SK-6600-TAN"]'))

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
