import requests
import os

OLLAMA_URL = "http://localhost:11434"

REVIEW_PROMPT = """You are FlakkCode, an expert code review assistant designed to help developers improve their code quality.

Review the following code and provide feedback in these categories:

1. **Bugs & Errors**: Logic errors, potential runtime issues, off-by-one errors
2. **Security**: Vulnerabilities like SQL injection, XSS, hardcoded secrets
3. **Best Practices**: Code style, naming conventions, DRY principle
4. **Performance**: Inefficiencies, unnecessary operations, optimization opportunities
5. **Readability**: Comments, structure, complexity

For each issue found:
- Explain WHAT the issue is
- Explain WHY it's a problem (educational focus)
- Show HOW to fix it with a code example

If the code is good, acknowledge what's done well.

Be encouraging but thorough - this is for learning.

Language: {language}

```{language}
{code}
```"""


def analyze_code(code, language="python", model="mistral", use_claude=False):
    """Analyze code using either Ollama or Claude API."""
    prompt = REVIEW_PROMPT.format(language=language, code=code)

    if use_claude:
        return _analyze_with_claude(prompt, language)
    else:
        return _analyze_with_ollama(prompt, model)


def _analyze_with_ollama(prompt, model="mistral"):
    """Analyze code using local Ollama model."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are FlakkCode, an expert code analyzer. Provide thorough, educational code reviews with markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            },
            timeout=300
        )

        if response.ok:
            data = response.json()
            return {
                "success": True,
                "review": data["message"]["content"],
                "engine": f"ollama/{model}"
            }
        else:
            return {
                "success": False,
                "error": f"Ollama error: {response.status_code}"
            }

    except requests.ConnectionError:
        return {
            "success": False,
            "error": "Cannot connect to Ollama. Make sure it is running."
        }
    except requests.Timeout:
        return {
            "success": False,
            "error": "Analysis timed out. Try a shorter code snippet."
        }


def _analyze_with_claude(prompt, language):
    """Analyze code using Claude API (optional fallback)."""
    try:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "No Anthropic API key configured."
            }

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "success": True,
            "review": message.content[0].text,
            "engine": "claude-sonnet"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Claude API error: {str(e)}"
        }
