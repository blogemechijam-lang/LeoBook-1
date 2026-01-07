import requests
import json
import os
import asyncio
from typing import Optional

class SemanticMatcher:
    def __init__(self, model: str = 'qwen3-vl:2b-custom'):
        """
        Initialize the SemanticMatcher for local LLM server (OpenAI-compatible endpoint).
        """
        self.model = model
        self.api_url = os.getenv("LLM_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "15"))  # Reduced from 60s to 15s for better performance
        self.cache = {}  # Add caching to avoid repeated LLM calls

    async def is_match(self, desc1: str, desc2: str, league: Optional[str] = None) -> Optional[bool]:
        """
        Determines if two match descriptions refer to the same football fixture.
        Asynchronous to allow non-blocking I/O.
        Returns None on error (instead of False) to allow fallback logic.
        """
        # Create cache key
        cache_key = f"{desc1}|{desc2}|{league or ''}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        context = ""
        if league:
            context = f"Both matches are in the league/competition: {league}. "

        prompt = (
            f"Are the following two football matches the same fixture?\n"
            f"Match A: {desc1}\n"
            f"Match B: {desc2}\n"
            f"{context}"
            f"Answer with exactly one word: 'Yes' if they are the same match, or 'No' if they are different."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 10,
        }

        try:
            def _do_request():
                return requests.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout
                )

            response = await asyncio.to_thread(_do_request)
            response.raise_for_status()

            data = response.json()
            content = data['choices'][0]['message']['content'].strip().lower()

            # Robust yes/no detection
            if content.startswith('yes'):
                result = True
            elif content.startswith('no'):
                result = False
            else:
                result = 'yes' in content

            # Cache the result
            self.cache[cache_key] = result
            return result

        except Exception as e:
            print(f"  [LLM Matcher Error] {e}")
            return None  # Return None instead of False to indicate error
