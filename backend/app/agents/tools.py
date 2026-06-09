"""
画像构建 + 资源生成专用工具集
"""
import json
from app.services.llm import chat_deepseek, chat_qwen


def ask_dimension(args: dict) -> str:
    """向用户提问某个画像维度"""
    dim_key = args.get("dim_key", "")
    dim_label = args.get("dim_label", "")
    question = args.get("question", "")

    return json.dumps({
        "type": "ask_user",
        "dim_key": dim_key,
        "dim_label": dim_label,
        "question": question or f"请分享一下你在「{dim_label}」方面的情况？",
        "hint": "前端应将此问题展示给用户，等待用户回答",
    }, ensure_ascii=False)


def extract_profile_dimension(args: dict) -> str:
    """从用户消息中提取画像维度数据"""
    dim_key = args.get("dim_key", "")
    dim_label = args.get("dim_label", "")
    user_text = args.get("user_text", "")

    if not user_text:
        return json.dumps({"error": "no user text to extract"})

    resp = chat_deepseek([{
        "role": "system",
        "content": f"根据用户描述，用一句话总结在「{dim_label}」维度的特征。返回JSON：{{\"{dim_key}\": \"一句话描述\"}}"
    }, {
        "role": "user",
        "content": user_text,
    }], temperature=0.3, max_tokens=100, json_mode=True)

    try:
        return json.dumps(json.loads(resp.choices[0].message.content.strip()), ensure_ascii=False)
    except json.JSONDecodeError:
        return json.dumps({dim_key: user_text[:100]})


def generate_report(args: dict) -> str:
    """生成最终画像报告"""
    profile_text = args.get("profile_text", "")

    resp = chat_deepseek([{
        "role": "system",
        "content": f"""你是学习画像分析师。根据数据生成一份优雅的画像报告。

{profile_text}

按以下结构输出纯文本报告（不要JSON、不要代码块）：

### 🌟 学习画像总览
2-3句话概括学习特质

### 🔍 多维分析
每个维度1-2句分析

### 📌 个性化学习建议
3条具体可执行的建议

### 🎯 推荐学习资源类型
适合的3种资源形式"""
    }], temperature=0.6, max_tokens=1500)

    report = resp.choices[0].message.content.strip()
    return json.dumps({
        "type": "report",
        "content": report,
    }, ensure_ascii=False)


def search_learning_resources(args: dict) -> str:
    """搜索学习资源"""
    topic = args.get("topic", "")
    resource_type = args.get("type", "all")  # courses, books, videos, articles

    resp = chat_deepseek([{
        "role": "system",
        "content": f"""你是学习资源推荐专家。推荐适合学习「{topic}」的{resource_type}资源。

返回JSON格式：
{{
    "resources": [
        {{"title": "资源名称", "type": "course/book/video/article", "url": "推荐搜索关键词（非真实URL）", "difficulty": "入门/中级/高级", "why": "推荐理由（1句话）"}}
    ],
    "learning_path": "推荐的学习路线（3-5步）",
    "estimated_time": "预估学习时长"
}}

推荐5个高质量资源，覆盖不同难度。只返回JSON。"""
    }], temperature=0.6, max_tokens=800, json_mode=True)

    try:
        data = json.loads(resp.choices[0].message.content.strip())
        data["type"] = "resources"
        return json.dumps(data, ensure_ascii=False)
    except json.JSONDecodeError:
        return json.dumps({"error": "资源搜索失败", "type": "resources"})


def final_answer(args: dict) -> str:
    """标记为最终回答"""
    return json.dumps({
        "type": "final",
        "content": args.get("text", ""),
    }, ensure_ascii=False)
