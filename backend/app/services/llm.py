"""LLM 客户端封装：Qwen(主力)、DeepSeek(推理)、Seedance(视频)、Mimo(多模态)"""
import httpx
from openai import OpenAI
from app.config import (
    QWEN_API_KEY, QWEN_MODEL, QWEN_BASE_URL,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL,
    SEEDANCE_API_KEY, SEEDANCE_MODEL, SEEDANCE_BASE_URL,
    MIMO_API_KEY, MIMO_BASE_URL,
)

http_client = httpx.Client(proxy="http://127.0.0.1:7897", timeout=60)

qwen = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL, http_client=http_client)
seedance = OpenAI(api_key=SEEDANCE_API_KEY, base_url=SEEDANCE_BASE_URL, http_client=http_client)
deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, http_client=http_client)
mimo = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL, http_client=http_client) if MIMO_BASE_URL else None


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


def chat_deepseek(messages: list, temperature=0.3, max_tokens=4096, json_mode=False, tools: list = None):
    """调用 DeepSeek"""
    kwargs = dict(
        model=DEEPSEEK_MODEL, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if tools:
        kwargs["tools"] = tools
    return deepseek.chat.completions.create(**kwargs)


def generate_wan_image(prompt: str, size: str = "1024*1024") -> str | None:
    """通义万相 wan2.6-t2i 生成画像插图"""
    import os, json, base64, time
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        return None
    try:
        resp = __import__("httpx").post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={"model": "wan2.6-t2i", "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
                  "parameters": {"prompt_extend": True, "watermark": False, "n": 1, "size": size}},
            timeout=120,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        choices = data.get("output", {}).get("choices", [])
        if not choices:
            return None
        content = choices[0].get("message", {}).get("content", [])
        img_url = None
        for item in content:
            if isinstance(item, dict) and "image" in item:
                img_url = item["image"]
                break
        if not img_url:
            return None
        img_resp = __import__("httpx").get(img_url, timeout=30)
        if img_resp.status_code != 200:
            return None
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "profiles")
        os.makedirs(static_dir, exist_ok=True)
        fname = f"profile_{int(time.time())}.png"
        fpath = os.path.join(static_dir, fname)
        with open(fpath, "wb") as f:
            f.write(img_resp.content)
        return f"/static/profiles/{fname}"
    except Exception as e:
        print(f"[Wan] {e}")
        return None
