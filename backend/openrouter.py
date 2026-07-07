"""Thin async OpenRouter client. Two entry points: stream a turn, and get JSON.

Kept deliberately small — this is the only module that talks to the network.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from . import config


class OpenRouterError(RuntimeError):
    pass


def _headers() -> dict:
    if not config.OPENROUTER_API_KEY:
        raise OpenRouterError(
            "OPENROUTER_API_KEY is not set. Export it before starting the server."
        )
    return {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # OpenRouter likes these for attribution; harmless if omitted.
        "HTTP-Referer": "https://github.com/roundtable",
        "X-Title": "The Roundtable",
    }


async def stream_chat(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.8,
    max_tokens: int = 320,
) -> AsyncIterator[str]:
    """Yield text chunks as the model generates them (SSE from OpenRouter)."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        async with client.stream(
            "POST",
            f"{config.OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        ) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", "replace")
                raise OpenRouterError(f"{resp.status_code}: {body[:500]}")
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                # `choices` can be present but empty (role/usage/keep-alive chunks),
                # so guard the index instead of relying on a missing-key default.
                choices = obj.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                chunk = delta.get("content")
                if chunk:
                    yield chunk


async def complete_json(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.0,
    max_tokens: int = 1200,
) -> dict:
    """Non-streaming call that asks for and parses a JSON object."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            f"{config.OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
    if resp.status_code >= 400:
        raise OpenRouterError(f"{resp.status_code}: {resp.text[:500]}")
    return _loads_lenient(_first_content(resp.json()))


async def complete_text(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.4,
    max_tokens: int = 600,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            f"{config.OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
    if resp.status_code >= 400:
        raise OpenRouterError(f"{resp.status_code}: {resp.text[:500]}")
    return _first_content(resp.json()).strip()


def _first_content(body: dict) -> str:
    """Pull the first message's content, with a clear error if the model returned
    no choices (moderation, provider hiccup) instead of a bare IndexError."""
    choices = body.get("choices") or []
    if not choices:
        err = body.get("error") or body
        raise OpenRouterError(f"Model returned no choices: {json.dumps(err)[:300]}")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise OpenRouterError("Model returned an empty message.")
    return content


def _loads_lenient(content: str) -> dict:
    """Some models wrap JSON in prose or fences. Recover the object."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(content[start : end + 1])
    raise OpenRouterError(f"Could not parse JSON from model output: {content[:200]}")
