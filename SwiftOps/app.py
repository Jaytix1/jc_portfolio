from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import requests
import json

from models import (
    init_db, get_db,
    create_manifest, get_manifest, get_all_manifests, get_upcoming_arrivals,
    update_manifest_totals, add_manifest_item, get_manifest_items,
    get_new_items_in_manifest, create_task, get_tasks, update_task_status,
    delete_task, get_dashboard_stats, get_top_products_by_volume,
    get_product_history, get_all_products, get_new_products
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

# SentinelAI integration
SENTINEL_API = "http://localhost:5002"


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

    return render_template('index.html',
                           page='dashboard',
                           stats=stats,
                           upcoming=upcoming,
                           tasks=tasks,
                           top_products=top_products)


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

    return render_template('index.html',
                           page='analytics',
                           top_products=top_products,
                           products=products,
                           new_products=new_products)


@app.route('/assistant')
def assistant_page():
    """AI Assistant page - powered by SentinelAI."""
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
    """
    Chat with AI assistant about manifest/inventory data.
    Routes through SentinelAI with context injection.
    """
    data = request.json
    user_message = data.get('message', '')

    # Build context from current data
    stats = get_dashboard_stats()
    upcoming = get_upcoming_arrivals()
    top_products = get_top_products_by_volume(days=30, limit=10)

    context = f"""You are SwiftOps Assistant, an AI helper for inventory and shipment management.

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
Be concise and actionable."""

    # Call SentinelAI
    try:
        response = requests.post(
            f"{SENTINEL_API}/api/chat",
            json={
                'messages': [
                    {'role': 'system', 'content': context},
                    {'role': 'user', 'content': user_message}
                ],
                'model': 'mistral',
                'persona': 'technical'
            },
            timeout=120
        )

        if response.ok:
            result = response.json()
            return jsonify({'response': result['response']})
        else:
            return jsonify({'error': 'AI service unavailable'}), 503

    except requests.ConnectionError:
        return jsonify({
            'error': 'Cannot connect to SentinelAI. Make sure it is running on port 5002.'
        }), 503
    except requests.Timeout:
        return jsonify({'error': 'AI request timed out'}), 504


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

    try:
        response = requests.post(
            f"{SENTINEL_API}/api/chat",
            json={
                'messages': [{'role': 'user', 'content': prompt}],
                'model': 'mistral',
                'persona': 'technical'
            },
            timeout=120
        )

        if response.ok:
            result = response.json()
            return jsonify({'analysis': result['response']})
        else:
            return jsonify({'error': 'AI service unavailable'}), 503

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Health Check
# ============================================

@app.route('/api/health')
def health():
    """Health check endpoint."""
    # Check SentinelAI connection
    sentinel_ok = False
    try:
        r = requests.get(f"{SENTINEL_API}/api/health", timeout=5)
        sentinel_ok = r.ok
    except:
        pass

    return jsonify({
        'status': 'healthy',
        'sentinel_ai_connected': sentinel_ok
    })


if __name__ == '__main__':
    app.run(debug=True, port=5003)
