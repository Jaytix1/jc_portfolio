from flask import Flask, render_template, request, jsonify
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

REVIEW_PROMPT = """You are FlakkAi, an expert code review assistant designed to help students and development teams improve their code quality.

IMPORTANT: First determine whether the input is a complete program or a code snippet/fragment.
- If it is a snippet or fragment (e.g. a single function, a few lines, a quick test), analyze ONLY what was provided. Do NOT flag missing entry points like main(), missing imports, or incomplete structure — the user is aware it is a fragment.
- If it is a complete program, apply full analysis including structure and entry points.

Review the code and provide feedback on any of the following that are actually relevant:

1. **Bugs & Errors**: Logic errors, potential runtime issues, off-by-one errors
2. **Security**: Vulnerabilities like SQL injection, XSS, hardcoded secrets
3. **Best Practices**: Code style, naming conventions, DRY principle
4. **Performance**: Inefficiencies, unnecessary operations, optimization opportunities
5. **Readability**: Comments, structure, complexity

For each issue found:
- Explain WHAT the issue is
- Explain WHY it's a problem (educational focus)
- Show HOW to fix it with a code example

If the code looks correct for what it is, say so clearly and positively.

Be encouraging but thorough - this is for learning.

Language: {language}

```{language}
{code}
```"""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/review', methods=['POST'])
def review_code():
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'python')

    if not code.strip():
        return jsonify({'error': 'No code provided'}), 400

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": REVIEW_PROMPT.format(language=language, code=code)
                }
            ]
        )

        review = message.content[0].text
        return jsonify({'review': review})

    except anthropic.APIError as e:
        return jsonify({'error': f'API error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
