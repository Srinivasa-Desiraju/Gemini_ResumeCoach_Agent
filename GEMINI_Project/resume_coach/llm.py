"""Lightweight caller for Gemini Flash 2.5 using Google's Generative API (API key mode).

This module implements a minimal HTTP client that calls the Generative API
when the environment variable `GOOGLE_API_KEY` is set. It is intentionally
small and has no heavy third-party dependencies so you can inspect and run it
in a dev container. If you prefer Vertex AI client libraries or service
account auth, we can add that later.
"""
import os
import json
import requests
from typing import Optional

DEFAULT_MODEL = 'gemini-2.5-flash'
DEFAULT_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta2/models/{model}:generate'


def _extract_text_from_response(resp_json: dict) -> str:
    # Try common keys used by Generative API responses.
    # The exact field name can change; this helper attempts a few fallbacks.
    if not isinstance(resp_json, dict):
        return ''
    # v1beta2 style: 'candidates' -> list of dicts with 'output' or 'content'
    if 'candidates' in resp_json and isinstance(resp_json['candidates'], list) and resp_json['candidates']:
        cand = resp_json['candidates'][0]
        for k in ('content', 'output', 'text'):
            if k in cand:
                return cand[k]
        # sometimes candidate has 'message' with 'content'
        if 'message' in cand and isinstance(cand['message'], dict):
            cont = cand['message'].get('content') or cand['message'].get('text')
            if isinstance(cont, str):
                return cont

    # v1 style: 'output' top-level
    if 'output' in resp_json and isinstance(resp_json['output'], str):
        return resp_json['output']

    # fallback: try to stringify the response
    return json.dumps(resp_json)


def call_gemini_flash(prompt: str, api_key: Optional[str] = None, model: str = DEFAULT_MODEL, max_output_tokens: int = 1024, temperature: float = 0.2) -> str:
    """Call Gemini Flash 2.5 via Google Generative API using an API key.

    Requires `api_key` (or environment var `GOOGLE_API_KEY`).
    Returns the model text on success, or an error message on failure.
    """
    api_key = api_key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise RuntimeError('GOOGLE_API_KEY not provided')

    endpoint = DEFAULT_ENDPOINT.format(model=model)
    url = endpoint + f'?key={api_key}'

    body = {
        'prompt': {'text': prompt},
        'temperature': temperature,
        'maxOutputTokens': max_output_tokens,
    }

    headers = {'Content-Type': 'application/json'}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=30)
    except Exception as e:
        return f'LLM request failed: {e}'

    if r.status_code != 200:
        return f'LLM request failed: {r.status_code} {r.text}'

    try:
        resp_json = r.json()
    except Exception:
        return r.text

    return _extract_text_from_response(resp_json)


if __name__ == '__main__':
    print('This module calls Gemini Flash when GOOGLE_API_KEY is set.')
