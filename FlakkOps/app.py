from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import requests
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

from models import (
    init_db, get_db,
    create_manifest, get_manifest, get_all_manifests, get_upcoming_arrivals,
    update_manifest_totals, add_manifest_item, get_manifest_items,
    get_new_items_in_manifest, create_task, get_tasks, update_task_status,
    delete_task, get_dashboard_stats, get_top_products_by_volume,
    get_product_history, get_all_products, get_new_products,
    get_weekly_units_chart, get_category_breakdown,
    get_yoy_chart_data, get_task_status_counts, get_manifest_timeline,
    get_product_sparklines
)
from pdf_parser import parse_manifest, get_manifest_summary

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'csv', 'xlsx', 'xls'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
init_db()

# FlakkCode integration
FLAKK_API = "http://localhost:5002"


def _demo_analysis(manifest, items, new_items):
    """Generate a data-driven analysis without FlakkAi."""
    top = sorted(items, key=lambda x: x['quantity'], reverse=True)[:5]
    top_lines = '\n'.join(f"- {i['sku']}: {i['description'][:40]} — {i['quantity']} units" for i in top)
    new_section = ''
    if new_items:
        new_lines = '\n'.join(f"- {i['sku']}: {i['description'][:40]}" for i in new_items)
        new_section = f"\n\n**New Products Detected ({len(new_items)})**\n{new_lines}\nAllocate floor space and set up signage before arrival."

    volume_note = 'above average' if manifest['total_units'] > 280 else 'within normal range'

    return f"""**Shipment Analysis — {manifest['arrival_day']} {manifest['arrival_date']}**

**Overview**
{manifest['total_skus']} SKUs · {manifest['total_units']:,} units · Volume is {volume_note} for a single truck.

**Top Items by Quantity**
{top_lines}{new_section}

**Recommendations**
1. Pre-stage the receiving area at least 1 hour before truck arrival
2. Verify quantities line-by-line against this manifest — flag discrepancies immediately
3. {"Set up new SKU locations before the truck arrives" if new_items else "Standard replenishment — prioritize shelf restocking for high-velocity SKUs"}
4. Update inventory counts in the system within 2 hours of receiving"""


def _demo_chat_response(message):
    """Keyword-matched canned response when FlakkAi is offline."""
    msg = message.lower()
    note = ''

    if any(w in msg for w in ['priorit', 'focus', 'should i', 'what first', 'important']):
        return """Here are your top priorities right now:

1. **High — Prepare for Monday truck** (330 units, 8 SKUs) — clear the receiving area and brief your team on the 2 new Spring SKUs
2. **High — Update inventory counts** after arrival, flagging any discrepancies immediately
3. **Medium — Prepare for Wednesday mid-week truck** (192 units, running/athletic) — straightforward replenishment
4. **Low — Complete in-progress review** of SK-3300-RED and SK-1200-MUL from last week's shipment""" + note

    elif any(w in msg for w in ['trend', 'pattern', 'concern', 'compar', 'year', 'volume']):
        return """Looking at your recent data:

- **YoY volume:** 2026 weekly units average ~293/week vs ~257/week in 2025 — a solid **14% increase**
- **Top performers:** SK-8750-BLK (Arch Fit) and SK-2330-WHT (Summits) consistently lead volume across all manifests
- **New product pace:** 4 new SKUs added this month — slightly elevated, worth monitoring floor space
- **No anomalies** detected in recent shipment sizes or frequencies""" + note

    elif any(w in msg for w in ['new product', 'new sku', 'spring', 'space', 'floor', 'display']):
        return """For the incoming new Spring 2026 products:

- **SK-SPNG-WHT** — Spring Stride Pro White (48 units, 12-pack cases)
- **SK-SPNG-BLU** — Spring Stride Pro Blue (48 units, 12-pack cases)

**Recommended prep:**
1. Allocate 4–6 linear feet in the Running category for the Spring Stride Pro line
2. Set up signage before the Monday truck arrives — 96 units total is a strong intro quantity
3. Check planogram for Running and identify display location in advance""" + note

    elif any(w in msg for w in ['how many', 'total', 'count', 'unit', 'quantity', 'expect']):
        return """Current volume snapshot:

- **This week incoming:** 522 units across 2 trucks (330 Mon + 192 Wed)
- **Last week received:** 204 units (Wednesday truck, fully processed)
- **Pending tasks:** 4 open, 2 high priority tied to Monday arrival
- **2026 vs 2025:** Running approximately 14% higher volume for this same period""" + note

    else:
        return """Here's your current operations overview:

**Incoming this week:** 2 trucks — Monday (330 units, 8 SKUs including 2 new Spring products) and Wednesday (192 units, 5 SKUs, running/athletic replenishment).

**Task status:** 4 pending tasks, 1 in progress. Two high-priority items require action before Monday's truck arrives.

**Top products this month:** Arch Fit Slip Resistant (SK-8750-BLK) and Summits Fast Attraction (SK-2330-WHT) continue to lead volume across all recent manifests.

**Recommendation:** Focus on Monday truck prep — largest incoming shipment with new SKUs that need floor setup before arrival.""" + note


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# ============================================
# Page Routes
# ============================================

@app.route('/')
def dashboard():
    """Main dashboard view."""
    stats = get_dashboard_stats()
    upcoming = get_upcoming_arrivals()
    tasks = get_tasks(status='pending', limit=5)
    top_products = get_top_products_by_volume(days=30, limit=5)
    weekly_chart = get_weekly_units_chart()
    category_breakdown = get_category_breakdown()
    incoming_preview = get_manifest_items(upcoming[0]['id']) if upcoming else []
    yoy_chart = get_yoy_chart_data()
    task_counts = get_task_status_counts()
    manifest_timeline = get_manifest_timeline()

    return render_template('index.html',
                           page='dashboard',
                           stats=stats,
                           upcoming=upcoming,
                           tasks=tasks,
                           top_products=top_products,
                           weekly_chart=weekly_chart,
                           category_breakdown=category_breakdown,
                           incoming_preview=incoming_preview,
                           yoy_chart=yoy_chart,
                           task_counts=task_counts,
                           manifest_timeline=manifest_timeline)


@app.route('/manifests')
def manifests_page():
    """Manifests list and upload page."""
    manifests = get_all_manifests(limit=50)
    return render_template('index.html',
                           page='manifests',
                           manifests=manifests)


@app.route('/manifest/<int:manifest_id>')
def manifest_detail(manifest_id):
    """Single manifest detail view."""
    manifest = get_manifest(manifest_id)
    if not manifest:
        return redirect(url_for('manifests_page'))

    items = get_manifest_items(manifest_id)
    new_items = get_new_items_in_manifest(manifest_id)
    summary = get_manifest_summary(items)

    return render_template('index.html',
                           page='manifest_detail',
                           manifest=manifest,
                           items=items,
                           new_items=new_items,
                           summary=summary)


@app.route('/tasks')
def tasks_page():
    """Tasks management page."""
    filter_status = request.args.get('status', None)
    tasks = get_tasks(status=filter_status, limit=100)
    return render_template('index.html',
                           page='tasks',
                           tasks=tasks,
                           filter_status=filter_status)


@app.route('/analytics')
def analytics_page():
    """Analytics and reporting page."""
    top_products = get_top_products_by_volume(days=90, limit=20)
    products = get_all_products()
    new_products = get_new_products()
    heatmap_data = get_yoy_chart_data(limit=8)
    product_sparklines = get_product_sparklines([p['sku'] for p in top_products[:10]])

    return render_template('index.html',
                           page='analytics',
                           top_products=top_products,
                           products=products,
                           new_products=new_products,
                           heatmap_data=heatmap_data,
                           product_sparklines=product_sparklines)


@app.route('/assistant')
def assistant_page():
    """AI Assistant page - powered by FlakkAi."""
    return render_template('index.html', page='assistant')


# ============================================
# API Routes - Manifests
# ============================================

@app.route('/api/manifest/upload', methods=['POST'])
def upload_manifest():
    """Upload and process a manifest PDF."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PDF, CSV, XLSX'}), 400

    # Get form data
    manifest_date = request.form.get('manifest_date', datetime.now().strftime('%Y-%m-%d'))
    arrival_day = request.form.get('arrival_day', 'Monday')
    notes = request.form.get('notes', '')

    # Save file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
    file.save(filepath)

    # Create manifest record
    manifest_id = create_manifest(saved_filename, manifest_date, arrival_day, notes)

    # Parse the file
    if filename.lower().endswith('.pdf'):
        parse_result = parse_manifest(filepath)

        # Add items to database
        new_product_count = 0
        for item in parse_result['items']:
            is_new = add_manifest_item(
                manifest_id,
                item['sku'],
                item['description'],
                item['quantity'],
                item.get('case_pack')
            )
            if is_new:
                new_product_count += 1

        # Update manifest totals
        summary = get_manifest_summary(parse_result['items'])
        update_manifest_totals(manifest_id, summary['total_skus'], summary['total_units'])

        # Auto-create tasks for new products
        if new_product_count > 0:
            manifest = get_manifest(manifest_id)
            create_task(
                f"Review {new_product_count} new product(s) from {arrival_day} truck",
                f"New SKUs detected in manifest. Review and set up locations.",
                priority='high',
                due_date=manifest['arrival_date'],
                manifest_id=manifest_id
            )

        return jsonify({
            'success': True,
            'manifest_id': manifest_id,
            'items_found': len(parse_result['items']),
            'new_products': new_product_count,
            'parse_method': parse_result['parse_method'],
            'errors': parse_result['errors']
        })

    # TODO: Handle CSV/XLSX
    return jsonify({
        'success': True,
        'manifest_id': manifest_id,
        'message': 'File uploaded. Manual processing required for non-PDF files.'
    })


@app.route('/api/manifests', methods=['GET'])
def api_get_manifests():
    """Get all manifests."""
    manifests = get_all_manifests()
    return jsonify({'manifests': manifests})


@app.route('/api/manifest/<int:manifest_id>', methods=['GET'])
def api_get_manifest(manifest_id):
    """Get manifest details."""
    manifest = get_manifest(manifest_id)
    if not manifest:
        return jsonify({'error': 'Manifest not found'}), 404

    items = get_manifest_items(manifest_id)
    return jsonify({
        'manifest': manifest,
        'items': items
    })


# ============================================
# API Routes - Tasks
# ============================================

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """Get tasks."""
    status = request.args.get('status')
    tasks = get_tasks(status=status)
    return jsonify({'tasks': tasks})


@app.route('/api/task', methods=['POST'])
def api_create_task():
    """Create a new task."""
    data = request.json
    task_id = create_task(
        title=data.get('title', 'Untitled Task'),
        description=data.get('description'),
        priority=data.get('priority', 'medium'),
        due_date=data.get('due_date'),
        manifest_id=data.get('manifest_id')
    )
    return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/task/<int:task_id>', methods=['PATCH'])
def api_update_task(task_id):
    """Update task status."""
    data = request.json
    status = data.get('status')
    if status:
        update_task_status(task_id, status)
    return jsonify({'success': True})


@app.route('/api/task/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """Delete a task."""
    delete_task(task_id)
    return jsonify({'success': True})


# ============================================
# API Routes - Analytics
# ============================================

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """Get dashboard statistics."""
    stats = get_dashboard_stats()
    return jsonify(stats)


@app.route('/api/products/top', methods=['GET'])
def api_top_products():
    """Get top products by volume."""
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 10, type=int)
    products = get_top_products_by_volume(days, limit)
    return jsonify({'products': products})


@app.route('/api/product/<sku>/history', methods=['GET'])
def api_product_history(sku):
    """Get quantity history for a product."""
    history = get_product_history(sku)
    return jsonify({'history': history})


# ============================================
# API Routes - AI Assistant
# ============================================

@app.route('/api/assistant/chat', methods=['POST'])
def assistant_chat():
    """Chat with Claude about manifest/inventory data."""
    data = request.json
    user_message = data.get('message', '')

    stats = get_dashboard_stats()
    upcoming = get_upcoming_arrivals()
    top_products = get_top_products_by_volume(days=30, limit=10)

    system_prompt = f"""You are FlakkOps Assistant, an AI helper for inventory and shipment management at a retail shoe store.

Current Status:
- Upcoming truck arrivals (next 7 days): {stats['upcoming_arrivals']}
- Pending tasks: {stats['pending_tasks']}
- Units expected this week: {stats['units_this_week']}
- Total SKUs tracked: {stats['total_skus']}
- New products this month: {stats['new_products_month']}

Upcoming Arrivals:
{json.dumps([{'date': m['arrival_date'], 'day': m['arrival_day'], 'skus': m['total_skus'], 'units': m['total_units']} for m in upcoming], indent=2) if upcoming else 'None scheduled'}

Top Products (Last 30 Days):
{json.dumps([{'sku': p['sku'], 'description': p['description'][:50], 'total_qty': p['total_quantity']} for p in top_products[:5]], indent=2) if top_products else 'No data yet'}

The user manages inventory receiving for trucks arriving every Monday and Wednesday.
Help them plan, prioritize, and make decisions about incoming shipments.
Be concise and actionable. Use markdown formatting."""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        return jsonify({'response': _demo_chat_response(user_message)})

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}]
        )
        return jsonify({'response': message.content[0].text})

    except Exception:
        return jsonify({'response': _demo_chat_response(user_message)})


@app.route('/api/manifest/<int:manifest_id>/analyze', methods=['POST'])
def analyze_manifest(manifest_id):
    """Get AI analysis of a specific manifest."""
    manifest = get_manifest(manifest_id)
    if not manifest:
        return jsonify({'error': 'Manifest not found'}), 404

    items = get_manifest_items(manifest_id)
    new_items = get_new_items_in_manifest(manifest_id)

    # Build analysis prompt
    prompt = f"""Analyze this incoming shipment manifest:

Arrival: {manifest['arrival_day']}, {manifest['arrival_date']}
Total SKUs: {manifest['total_skus']}
Total Units: {manifest['total_units']}
New Products: {len(new_items)}

Top 10 Items by Quantity:
{chr(10).join([f"- {item['sku']}: {item['description'][:40]} - {item['quantity']} units" for item in sorted(items, key=lambda x: x['quantity'], reverse=True)[:10]])}

{"New Products:" + chr(10) + chr(10).join([f"- {item['sku']}: {item['description'][:40]} - {item['quantity']} units" for item in new_items]) if new_items else ""}

Provide:
1. Key observations about this shipment
2. Potential issues or things to watch
3. Recommended preparation tasks
4. Comparison notes (if this seems higher/lower volume than typical)

Be specific and actionable."""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        return jsonify({'analysis': _demo_analysis(manifest, items, new_items)})

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return jsonify({'analysis': message.content[0].text})

    except Exception:
        return jsonify({'analysis': _demo_analysis(manifest, items, new_items)})


# ============================================
# Demo Utilities
# ============================================

@app.route('/api/sample-manifest')
def sample_manifest():
    """Download a sample manifest CSV for demo purposes."""
    from flask import Response
    content = (
        "SKU,Description,Quantity,CasePack,Weight\n"
        "SK-8750-BLK,Arch Fit Slip Resistant - Black,48,6,18.2\n"
        "SK-8751-NVY,Arch Fit Slip Resistant - Navy,36,6,18.2\n"
        "SK-2330-WHT,Summits Fast Attraction - White,60,12,12.4\n"
        "SK-2331-GRY,Summits Fast Attraction - Grey,48,12,12.4\n"
        "SK-4040-PNK,D'Lites Fresh Start - Pink,36,6,16.8\n"
        "SK-6600-TAN,Relaxed Fit Expected Avillo - Tan,42,6,19.5\n"
        "SK-9010-BLK,GO Run Consistent - Black,24,6,13.1\n"
        "SK-5500-GRN,Max Cushioning Premier - Green,18,6,14.6\n"
    )
    return Response(
        content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=sample_manifest.csv'}
    )


# ============================================
# Health Check
# ============================================

@app.route('/api/health')
def health():
    """Health check endpoint."""
    # Check FlakkAi connection
    flakk_ok = False
    try:
        r = requests.get(f"{FLAKK_API}/api/health", timeout=5)
        flakk_ok = r.ok
    except:
        pass

    return jsonify({
        'status': 'healthy',
        'flakk_ai_connected': flakk_ok
    })


if __name__ == '__main__':
    app.run(debug=True, port=5003)
