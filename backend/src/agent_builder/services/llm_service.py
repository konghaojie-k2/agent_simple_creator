# -*- coding: utf-8 -*-
"""LLM Service module for agent builder.

This module provides LLM client support for multiple providers (DeepSeek, Qwen, OpenAI, etc.)
using OpenAI-compatible API format.
"""

import json
from typing import AsyncGenerator, Optional

import httpx

from agent_builder.core.config import settings


class LLMResponse:
    """LLM response container."""

    def __init__(
        self,
        content: str,
        thinking: Optional[str] = None,
        tool_calls: Optional[list] = None,
        finish_reason: str = "stop",
        usage: Optional[dict] = None,
    ):
        self.content = content
        self.thinking = thinking
        self.tool_calls = tool_calls
        self.finish_reason = finish_reason
        self.usage = usage


class LLMClient:
    """OpenAI-compatible LLM client supporting multiple providers."""

    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str = "gpt-4",
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout

        # Normalize api_base - ensure it has /v1 suffix for OpenAI-compatible APIs
        if not self.api_base.endswith("/v1"):
            self.api_base = f"{self.api_base}/v1"

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def generate(
        self,
        messages: list[dict],
        tools: Optional[list] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions
            stream: Whether to stream the response

        Returns:
            LLMResponse object
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        if tools:
            # Convert tools to OpenAI function calling format
            payload["tools"] = tools

        # Remove stream from payload if False (API might not support it)
        if not stream:
            payload.pop("stream", None)

        try:
            response = await self._client.post(
                f"{self.api_base}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Handle streaming response
            if stream:
                return data  # Return raw data for streaming

            # Parse response
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            # Extract content
            content = message.get("content", "")

            # Extract thinking (for models that support it like DeepSeek)
            thinking = message.get("thinking") or message.get("reasoning")

            # Extract tool calls
            tool_calls = None
            if message.get("tool_calls"):
                tool_calls = []
                for tc in message["tool_calls"]:
                    tool_calls.append({
                        "id": tc.get("id"),
                        "type": tc.get("type"),
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": json.loads(tc["function"]["arguments"]),
                        },
                    })

            # Extract usage
            usage = data.get("usage")

            return LLMResponse(
                content=content,
                thinking=thinking,
                tool_calls=tool_calls,
                finish_reason=choice.get("finish_reason", "stop"),
                usage=usage,
            )

        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"LLM request failed: {str(e)}")

    async def generate_stream(
        self,
        messages: list[dict],
        tools: Optional[list] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions

        Yields:
            Streamed response chunks
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools

        try:
            async with self._client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            choice = data.get("choices", [{}])[0]
                            delta = choice.get("delta", {})

                            # Yield content delta
                            if delta.get("content"):
                                yield delta["content"]

                            # Yield thinking delta
                            if delta.get("thinking"):
                                yield f"[Thinking: {delta['thinking']}]"

                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            yield f"data: {json.dumps({'error': f'LLM API error: {e.response.status_code} - {e.response.text}'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'LLM request failed: {str(e)}'})}\n\n"
