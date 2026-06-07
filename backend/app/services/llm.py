"""LLM 客户端封装：Qwen(主力)、DeepSeek(推理)、Seedance(视频)、Mimo(多模态)"""
from openai import OpenAI
from app.config import (
    QWEN_API_KEY, QWEN_MODEL, QWEN_BASE_URL,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL,
    SEEDANCE_API_KEY, SEEDANCE_MODEL, SEEDANCE_BASE_URL,
    MIMO_API_KEY, MIMO_BASE_URL,
)

qwen = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)
deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
seedance = OpenAI(api_key=SEEDANCE_API_KEY, base_url=SEEDANCE_BASE_URL)
mimo = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL) if MIMO_BASE_URL else None


def chat_qwen(messages: list, temperature=0.7, max_tokens=2048, json_mode=False):
    """调用千问主力模型"""
    kwargs = dict(
        model=QWEN_MODEL, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    return qwen.chat.completions.create(**kwargs)


def chat_qwen_stream(messages: list, temperature=0.7, max_tokens=2048):
    """流式调用千问"""
    return qwen.chat.completions.create(
        model=QWEN_MODEL, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
        stream=True,
    )


def chat_deepseek(messages: list, temperature=0.3, max_tokens=4096):
    """调用 DeepSeek（复杂推理）"""
    return deepseek.chat.completions.create(
        model=DEEPSEEK_MODEL, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
    )
