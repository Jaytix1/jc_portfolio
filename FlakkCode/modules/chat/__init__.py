import requests


OLLAMA_URL = "http://localhost:11434"

SYSTEM_PROMPTS = {
    "default": (
        "You are FlakkAi, a helpful and knowledgeable AI assistant. "
        "You are running locally via Ollama, fully self-hosted. "
        "Be concise, accurate, and helpful. Use markdown formatting when appropriate."
    ),
    "creative": (
        "You are FlakkAi in Creative mode. You help with writing, brainstorming, "
        "and creative tasks. Be imaginative and offer unique perspectives while remaining helpful."
    ),
    "technical": (
        "You are FlakkAi in Technical mode. You specialize in explaining technical concepts, "
        "answering engineering questions, and helping with system design. "
        "Be precise and thorough in your explanations."
    ),
}


def get_available_models():
    """Fetch list of models available in Ollama."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.ok:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
    except requests.ConnectionError:
        pass
    return []


def chat(messages, model="mistral", persona="default"):
    """Send a chat request to Ollama and return the response."""
    system_prompt = SYSTEM_PROMPTS.get(persona, SYSTEM_PROMPTS["default"])

    ollama_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        ollama_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": ollama_messages,
                "stream": False
            },
            timeout=300
        )

        if response.ok:
            data = response.json()
            return {
                "success": True,
                "response": data["message"]["content"],
                "model": model
            }
        else:
            return {
                "success": False,
                "error": f"Ollama error: {response.status_code}"
            }

    except requests.ConnectionError:
        return {
            "success": False,
            "error": "Cannot connect to Ollama. Make sure it is running (ollama serve)."
        }
    except requests.Timeout:
        return {
            "success": False,
            "error": "Request timed out. The model may be loading."
        }


def stream_chat(messages, model="mistral", persona="default"):
    """Send a streaming chat request to Ollama."""
    system_prompt = SYSTEM_PROMPTS.get(persona, SYSTEM_PROMPTS["default"])

    ollama_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        ollama_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": ollama_messages,
                "stream": True
            },
            stream=True,
            timeout=300
        )

        if response.ok:
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if not data.get("done", False):
                        yield data["message"]["content"]

    except requests.ConnectionError:
        yield "[Error: Cannot connect to Ollama]"
