from flask import Flask, render_template, request, jsonify, Response
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Import modules
from modules.chat import chat, stream_chat, get_available_models, SYSTEM_PROMPTS
from modules.code import analyze_code


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle chat messages via FlakkChat."""
    data = request.json
    messages = data.get('messages', [])
    model = data.get('model', 'mistral')
    persona = data.get('persona', 'default')

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    result = chat(messages, model=model, persona=persona)

    if result['success']:
        return jsonify({
            'response': result['response'],
            'model': result['model']
        })
    else:
        return jsonify({'error': result['error']}), 500


@app.route('/api/chat/stream', methods=['POST'])
def api_chat_stream():
    """Handle streaming chat messages."""
    data = request.json
    messages = data.get('messages', [])
    model = data.get('model', 'mistral')
    persona = data.get('persona', 'default')

    def generate():
        for chunk in stream_chat(messages, model=model, persona=persona):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/code/review', methods=['POST'])
def api_code_review():
    """Handle code analysis via FlakkCode."""
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'python')
    model = data.get('model', 'mistral')
    use_claude = data.get('use_claude', False)

    if not code.strip():
        return jsonify({'error': 'No code provided'}), 400

    result = analyze_code(
        code=code,
        language=language,
        model=model,
        use_claude=use_claude
    )

    if result['success']:
        return jsonify({
            'review': result['review'],
            'engine': result['engine']
        })
    else:
        return jsonify({'error': result['error']}), 500


@app.route('/api/models', methods=['GET'])
def api_models():
    """Get available Ollama models."""
    models = get_available_models()
    return jsonify({'models': models})


@app.route('/api/personas', methods=['GET'])
def api_personas():
    """Get available chat personas."""
    personas = {k: v[:80] + '...' for k, v in SYSTEM_PROMPTS.items()}
    return jsonify({'personas': personas})


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    models = get_available_models()
    return jsonify({
        'status': 'healthy',
        'ollama_connected': len(models) > 0,
        'models_available': models
    })


if __name__ == '__main__':
    app.run(debug=True, port=5002)
