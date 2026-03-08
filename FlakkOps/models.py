import sqlite3
from datetime import datetime, timedelta
import os

DATABASE = 'flakkops.db'


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Manifests table - stores uploaded manifest metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manifests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            manifest_date DATE,
            arrival_date DATE,
            arrival_day TEXT CHECK(arrival_day IN ('Monday', 'Wednesday')),
            total_skus INTEGER DEFAULT 0,
            total_units INTEGER DEFAULT 0,
            notes TEXT,
            processed BOOLEAN DEFAULT 0
        )
    ''')

    # Products table - master list of all products seen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT,
            category TEXT,
            first_seen DATE DEFAULT CURRENT_DATE,
            is_new BOOLEAN DEFAULT 1,
            notes TEXT
        )
    ''')

    # Manifest items - line items from each manifest
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manifest_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manifest_id INTEGER NOT NULL,
            product_id INTEGER,
            sku TEXT NOT NULL,
            description TEXT,
            quantity INTEGER DEFAULT 0,
            case_pack INTEGER,
            weight REAL,
            is_new_product BOOLEAN DEFAULT 0,
            FOREIGN KEY (manifest_id) REFERENCES manifests(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Tasks table - action items generated from manifests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manifest_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')) DEFAULT 'medium',
            status TEXT CHECK(status IN ('pending', 'in_progress', 'completed')) DEFAULT 'pending',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (manifest_id) REFERENCES manifests(id)
        )
    ''')

    # Historical weekly data - aggregated for year-over-year comparison
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            total_skus INTEGER DEFAULT 0,
            total_units INTEGER DEFAULT 0,
            top_products TEXT,
            notes TEXT,
            UNIQUE(year, week_number)
        )
    ''')

    conn.commit()
    conn.close()


# ============================================
# Manifest Functions
# ============================================

def create_manifest(filename, manifest_date, arrival_day, notes=None):
    """Create a new manifest record."""
    conn = get_db()
    cursor = conn.cursor()

    # Calculate arrival date (1 week after manifest date, on the specified day)
    manifest_dt = datetime.strptime(manifest_date, '%Y-%m-%d')
    days_ahead = 0 if arrival_day == 'Monday' else 2  # Monday=0, Wednesday=2
    days_until = (days_ahead - manifest_dt.weekday() + 7) % 7
    if days_until == 0:
        days_until = 7  # Next week
    arrival_date = manifest_dt + timedelta(days=days_until)

    cursor.execute('''
        INSERT INTO manifests (filename, manifest_date, arrival_date, arrival_day, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, manifest_date, arrival_date.strftime('%Y-%m-%d'), arrival_day, notes))

    manifest_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return manifest_id


def get_manifest(manifest_id):
    """Get a single manifest by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM manifests WHERE id = ?', (manifest_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None


def get_all_manifests(limit=50):
    """Get all manifests, most recent first."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM manifests
        ORDER BY manifest_date DESC, upload_date DESC
        LIMIT ?
    ''', (limit,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_upcoming_arrivals():
    """Get manifests with trucks arriving in the next 7 days."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM manifests
        WHERE arrival_date BETWEEN DATE('now') AND DATE('now', '+7 days')
        ORDER BY arrival_date ASC
    ''')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def update_manifest_totals(manifest_id, total_skus, total_units):
    """Update manifest totals after processing."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE manifests
        SET total_skus = ?, total_units = ?, processed = 1
        WHERE id = ?
    ''', (total_skus, total_units, manifest_id))
    conn.commit()
    conn.close()


# ============================================
# Product Functions
# ============================================

def get_or_create_product(sku, name=None, category=None):
    """Get existing product or create new one."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM products WHERE sku = ?', (sku,))
    result = cursor.fetchone()

    if result:
        conn.close()
        return dict(result), False  # Existing product

    # Create new product
    cursor.execute('''
        INSERT INTO products (sku, name, category, is_new)
        VALUES (?, ?, ?, 1)
    ''', (sku, name, category))
    product_id = cursor.lastrowid
    conn.commit()

    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result), True  # New product


def mark_product_not_new(sku):
    """Mark a product as no longer new."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET is_new = 0 WHERE sku = ?', (sku,))
    conn.commit()
    conn.close()


def get_all_products():
    """Get all products."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY name')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_new_products():
    """Get products marked as new."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE is_new = 1 ORDER BY first_seen DESC')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================
# Manifest Items Functions
# ============================================

def add_manifest_item(manifest_id, sku, description, quantity, case_pack=None, weight=None):
    """Add a line item to a manifest."""
    conn = get_db()
    cursor = conn.cursor()

    # Get or create product
    product, is_new = get_or_create_product(sku, description)

    cursor.execute('''
        INSERT INTO manifest_items (manifest_id, product_id, sku, description, quantity, case_pack, weight, is_new_product)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (manifest_id, product['id'], sku, description, quantity, case_pack, weight, is_new))

    conn.commit()
    conn.close()
    return is_new


def get_manifest_items(manifest_id):
    """Get all items for a manifest."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT mi.*, p.category, p.is_new as product_is_new
        FROM manifest_items mi
        LEFT JOIN products p ON mi.product_id = p.id
        WHERE mi.manifest_id = ?
        ORDER BY mi.quantity DESC
    ''', (manifest_id,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_new_items_in_manifest(manifest_id):
    """Get only new products in a manifest."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM manifest_items
        WHERE manifest_id = ? AND is_new_product = 1
        ORDER BY quantity DESC
    ''', (manifest_id,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


# ============================================
# Task Functions
# ============================================

def create_task(title, description=None, priority='medium', due_date=None, manifest_id=None):
    """Create a new task."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (manifest_id, title, description, priority, due_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (manifest_id, title, description, priority, due_date))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_tasks(status=None, limit=50):
    """Get tasks, optionally filtered by status."""
    conn = get_db()
    cursor = conn.cursor()

    if status:
        cursor.execute('''
            SELECT t.*, m.arrival_date, m.arrival_day
            FROM tasks t
            LEFT JOIN manifests m ON t.manifest_id = m.id
            WHERE t.status = ?
            ORDER BY t.due_date ASC, t.priority DESC
            LIMIT ?
        ''', (status, limit))
    else:
        cursor.execute('''
            SELECT t.*, m.arrival_date, m.arrival_day
            FROM tasks t
            LEFT JOIN manifests m ON t.manifest_id = m.id
            ORDER BY t.status ASC, t.due_date ASC, t.priority DESC
            LIMIT ?
        ''', (limit,))

    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def update_task_status(task_id, status):
    """Update task status."""
    conn = get_db()
    cursor = conn.cursor()

    if status == 'completed':
        cursor.execute('''
            UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, task_id))
    else:
        cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))

    conn.commit()
    conn.close()


def delete_task(task_id):
    """Delete a task."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()


# ============================================
# Analytics Functions
# ============================================

def get_historical_comparison(week_number, current_year=None):
    """Get same-week comparison across years."""
    if current_year is None:
        current_year = datetime.now().year

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM weekly_history
        WHERE week_number = ?
        ORDER BY year DESC
    ''', (week_number,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_product_history(sku, limit=52):
    """Get quantity history for a specific product."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT mi.quantity, m.manifest_date, m.arrival_date
        FROM manifest_items mi
        JOIN manifests m ON mi.manifest_id = m.id
        WHERE mi.sku = ?
        ORDER BY m.manifest_date DESC
        LIMIT ?
    ''', (sku, limit))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_top_products_by_volume(days=30, limit=10):
    """Get top products by total quantity in recent period."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT mi.sku, mi.description, SUM(mi.quantity) as total_quantity, COUNT(*) as appearances
        FROM manifest_items mi
        JOIN manifests m ON mi.manifest_id = m.id
        WHERE m.manifest_date >= DATE('now', ?)
        GROUP BY mi.sku
        ORDER BY total_quantity DESC
        LIMIT ?
    ''', (f'-{days} days', limit))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_dashboard_stats():
    """Get summary statistics for dashboard."""
    conn = get_db()
    cursor = conn.cursor()

    stats = {}

    # Upcoming arrivals count
    cursor.execute('''
        SELECT COUNT(*) FROM manifests
        WHERE arrival_date BETWEEN DATE('now') AND DATE('now', '+7 days')
    ''')
    stats['upcoming_arrivals'] = cursor.fetchone()[0]

    # Pending tasks count
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
    stats['pending_tasks'] = cursor.fetchone()[0]

    # New products this month
    cursor.execute('''
        SELECT COUNT(*) FROM products
        WHERE first_seen >= DATE('now', '-30 days')
    ''')
    stats['new_products_month'] = cursor.fetchone()[0]

    # Total SKUs tracked
    cursor.execute("SELECT COUNT(*) FROM products")
    stats['total_skus'] = cursor.fetchone()[0]

    # Units expected this week
    cursor.execute('''
        SELECT COALESCE(SUM(total_units), 0) FROM manifests
        WHERE arrival_date BETWEEN DATE('now') AND DATE('now', '+7 days')
    ''')
    stats['units_this_week'] = cursor.fetchone()[0]

    conn.close()
    return stats


def get_weekly_units_chart(limit=8):
    """Last N weeks of units from weekly_history for 2026, oldest first."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT week_number, total_units
        FROM weekly_history
        WHERE year = 2026
        ORDER BY week_number DESC
        LIMIT ?
    ''', (limit,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in reversed(results)]


def get_category_breakdown():
    """Product count grouped by category (COALESCE NULL → 'Other')."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(category, 'Other') as category, COUNT(*) as count
        FROM products
        GROUP BY COALESCE(category, 'Other')
        ORDER BY count DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_yoy_chart_data(limit=8):
    """2026 + 2025 units side-by-side by week_number, oldest first."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT h26.week_number,
               h26.total_units AS units_2026,
               COALESCE(h25.total_units, 0) AS units_2025
        FROM weekly_history h26
        LEFT JOIN weekly_history h25
            ON h25.week_number = h26.week_number AND h25.year = 2025
        WHERE h26.year = 2026
        ORDER BY h26.week_number DESC
        LIMIT ?
    ''', (limit,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in reversed(results)]


def get_task_status_counts():
    """Returns {status: count} dict."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT status, COUNT(*) as count FROM tasks GROUP BY status')
    results = cursor.fetchall()
    conn.close()
    return {row['status']: row['count'] for row in results}


def get_manifest_timeline():
    """All manifests sorted by arrival_date ASC."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT arrival_date, arrival_day, total_units, total_skus, processed
        FROM manifests
        ORDER BY arrival_date ASC
    ''')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_product_sparklines(skus):
    """Returns {sku: [qty, qty, ...]} ordered by manifest_date ASC per SKU."""
    conn = get_db()
    cursor = conn.cursor()
    result = {}
    for sku in skus:
        cursor.execute('''
            SELECT mi.quantity
            FROM manifest_items mi
            JOIN manifests m ON mi.manifest_id = m.id
            WHERE mi.sku = ?
            ORDER BY m.manifest_date ASC
        ''', (sku,))
        rows = cursor.fetchall()
        result[sku] = [row['quantity'] for row in rows]
    conn.close()
    return result


# Initialize database when module is imported
if not os.path.exists(DATABASE):
    init_db()
