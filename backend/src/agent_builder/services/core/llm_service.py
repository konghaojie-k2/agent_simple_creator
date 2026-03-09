# -*- coding: utf-8 -*-
"""LLM Service module for agent builder.

This module provides LLM client support for multiple providers (DeepSeek, Qwen, OpenAI, etc.)
using OpenAI-compatible API format.
"""

import json
from typing import AsyncGenerator, List, Optional

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
        provider_type: str = None,
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.provider_type = provider_type

        # Normalize api_base - ensure it has /v1 suffix for OpenAI-compatible APIs
        # Skip for Ollama (local) - it doesn't use /v1
        self.is_ollama = "localhost:11434" in self.api_base
        if not self.is_ollama and not self.api_base.endswith("/v1"):
            self.api_base = f"{self.api_base}/v1"

        # Build headers - Ollama doesn't need Authorization header
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:  # Only add Authorization if API key is provided
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=headers,
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
            # Use different endpoint for Ollama
            if self.is_ollama:
                response = await self._client.post(
                    f"{self.api_base}/api/chat",
                    json=payload,
                )
                response.raise_for_status()

                # Ollama might return streaming response even with stream=false
                # Handle multiple JSON objects (newline-separated)
                text = response.text.strip()
                if "\n" in text:
                    # Multiple JSON objects - it's a streaming response
                    # Collect content from all chunks
                    full_content = ""
                    full_thinking = ""
                    last_data = None

                    lines = text.split("\n")
                    for line in lines:
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                last_data = chunk
                                # Accumulate content
                                msg = chunk.get("message", {})
                                if msg.get("content"):
                                    full_content += msg.get("content", "")
                                if msg.get("thinking"):
                                    full_thinking += msg.get("thinking", "")
                            except:
                                continue

                    # Use the last complete data for metadata
                    data = last_data or {}
                    # Override message with accumulated content
                    if full_content or full_thinking:
                        data["message"] = {
                            "content": full_content,
                            "thinking": full_thinking if full_thinking else None
                        }
                else:
                    # Single JSON object
                    data = response.json()
            else:
                response = await self._client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            # Handle streaming response
            if stream:
                return data  # Return raw data for streaming

            # Parse response - Ollama format is different
            if self.is_ollama:
                # Ollama response format: { "message": { "role": "assistant", "content": "..." }, ... }
                message = data.get("message", {})
                content = message.get("content", "")
                thinking = None
                tool_calls = None
            else:
                # OpenAI format
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

            # Get finish_reason
            if self.is_ollama:
                finish_reason = data.get("done", False)
                finish_reason = "stop" if finish_reason else "length"
            else:
                finish_reason = choice.get("finish_reason", "stop")

            return LLMResponse(
                content=content,
                thinking=thinking,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
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
            # Use different endpoint for Ollama
            if self.is_ollama:
                endpoint = f"{self.api_base}/api/chat"
            else:
                endpoint = f"{self.api_base}/chat/completions"

            async with self._client.stream(
                "POST",
                endpoint,
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    # Handle Ollama format (JSON per line)
                    if self.is_ollama:
                        try:
                            data = json.loads(line)
                            if data.get("done"):
                                break
                            message = data.get("message", {})
                            content = message.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

                    # Handle OpenAI format
                    elif line.startswith("data: "):
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

    async def generate_embedding(
        self,
        text: str,
        embedding_model: Optional[str] = None,
    ) -> List[float]:
        """Generate embedding for text using embedding model.

        Args:
            text: Text to generate embedding for
            embedding_model: Override default embedding model (e.g., "qwen3-embedding:4b")

        Returns:
            List of floats representing the embedding vector
        """
        model = embedding_model or self.model

        # For Ollama, use /api/embeddings endpoint
        if self.is_ollama:
            payload = {
                "model": model,
                "prompt": text,
            }
            try:
                response = await self._client.post(
                    f"{self.api_base}/api/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                embedding = data.get("embedding", [])
                return embedding
            except httpx.HTTPStatusError as e:
                raise Exception(f"Embedding API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                raise Exception(f"Embedding request failed: {str(e)}")
        else:
            # OpenAI-compatible API format
            payload = {
                "input": text,
                "model": model,
            }
            try:
                response = await self._client.post(
                    f"{self.api_base}/embeddings",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                embedding = data.get("data", [{}])[0].get("embedding", [])
                return embedding
            except httpx.HTTPStatusError as e:
                raise Exception(f"Embedding API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                raise Exception(f"Embedding request failed: {str(e)}")
