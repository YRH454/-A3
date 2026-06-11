"""LLM 客户端封装：Qwen(主力)、DeepSeek(推理)、Claude(课程)、Gemini(多模态)、Seedance(视频)、Mimo(多模态)"""

import json
import logging
import httpx
from openai import OpenAI
from app.config import (
    QWEN_API_KEY, QWEN_MODEL, QWEN_BASE_URL,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL,
    SEEDANCE_API_KEY, SEEDANCE_MODEL, SEEDANCE_BASE_URL,
    MIMO_API_KEY, MIMO_BASE_URL,
    CLAUDE_API_KEY, CLAUDE_MODEL, CLAUDE_BASE_URL,
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_BASE_URL,
)

logger = logging.getLogger(__name__)

# 代理配置：环境变量 HTTPS_PROXY 或 HTTP_PROXY，否则直连
import os as _os
_proxy_url = _os.getenv("HTTPS_PROXY") or _os.getenv("HTTP_PROXY") or None
if _proxy_url:
    logger.info(f"使用代理: {_proxy_url}")
else:
    logger.info("未配置代理，直连 API")

http_client = httpx.Client(proxy=_proxy_url, timeout=60)
http_client_long = httpx.Client(proxy=_proxy_url, timeout=120)

qwen = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL, http_client=http_client)
seedance = OpenAI(api_key=SEEDANCE_API_KEY, base_url=SEEDANCE_BASE_URL, http_client=http_client)
deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, http_client=http_client)
mimo = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL, http_client=http_client) if MIMO_BASE_URL else None


# ─── OpenAI 兼容响应模拟 ──────────────────────────────

class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    """模拟 openai 响应对象，使不同 API 返回格式兼容"""
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


# ─── Qwen ─────────────────────────────────────────────

def chat_qwen(messages: list, temperature=0.7, max_tokens=2048, json_mode=False, tools: list = None):
    kwargs = dict(
        model=QWEN_MODEL, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if tools:
        kwargs["tools"] = tools
    return qwen.chat.completions.create(**kwargs)


def chat_qwen_stream(messages: list, temperature=0.7, max_tokens=2048):
    return qwen.chat.completions.create(
        model=QWEN_MODEL, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
        stream=True,
    )


# ─── DeepSeek ─────────────────────────────────────────

def chat_deepseek(messages: list, temperature=0.3, max_tokens=4096, json_mode=False, tools: list = None):
    kwargs = dict(
        model=DEEPSEEK_MODEL, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if tools:
        kwargs["tools"] = tools
    return deepseek.chat.completions.create(**kwargs)


# ─── Claude (Anthropic Messages API) ──────────────────

def chat_claude(messages: list, temperature=0.5, max_tokens=4096, json_mode=False, tools: list = None):
    """调用 Claude（Anthropic Messages API）。

    将 OpenAI 格式的 messages 转换为 Anthropic 格式，
    返回兼容 openai 响应对象。
    """
    if not CLAUDE_API_KEY:
        raise RuntimeError("CLAUDE_API_KEY 未配置")

    # 转换消息格式
    system_prompt = ""
    anthropic_messages = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            system_prompt = content
        elif role in ("user", "assistant"):
            anthropic_messages.append({"role": role, "content": content})
        elif role == "tool":
            anthropic_messages.append({
                "role": "user",
                "content": f"[Tool Result]\n{content}",
            })

    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": anthropic_messages,
    }
    if system_prompt:
        body["system"] = system_prompt

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    try:
        resp = http_client_long.post(
            f"{CLAUDE_BASE_URL}/v1/messages",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        # 提取文本内容
        content_blocks = data.get("content", [])
        text_parts = []
        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return _FakeResponse("\n".join(text_parts))
    except httpx.HTTPStatusError as e:
        logger.error(f"Claude API 错误: {e.response.status_code} {e.response.text[:500]}")
        raise RuntimeError(f"Claude API 返回 {e.response.status_code}") from e


# ─── Gemini (Google Generative AI) ────────────────────

def chat_gemini(messages: list, temperature=0.6, max_tokens=4096, json_mode=False, tools: list = None):
    """调用 Gemini（Google AI API）。

    将 OpenAI 格式的 messages 转换为 Gemini 格式，
    返回兼容 openai 响应对象。
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY 未配置")

    base_url = GEMINI_BASE_URL or "https://generativelanguage.googleapis.com"

    # 转换消息格式
    system_instruction = ""
    contents = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            system_instruction = content
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        elif role == "tool":
            contents.append({
                "role": "user",
                "parts": [{"text": f"[Tool Result]\n{content}"}],
            })

    body = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if system_instruction:
        body["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    try:
        resp = http_client_long.post(
            f"{base_url}/v1beta/models/{GEMINI_MODEL}:generateContent",
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        # 提取文本内容
        candidates = data.get("candidates", [])
        text_parts = []
        for candidate in candidates:
            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    text_parts.append(part["text"])
        return _FakeResponse("\n".join(text_parts))
    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API 错误: {e.response.status_code} {e.response.text[:500]}")
        raise RuntimeError(f"Gemini API 返回 {e.response.status_code}") from e
