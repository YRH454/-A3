"""学习报告 API — 数据聚合 + AI评估"""

import json
import logging
from fastapi import APIRouter
from app.database import query
from app.services.llm import chat_deepseek

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/report", tags=["report"])


@router.get("/summary")
def get_report_summary(user_id: int):
    """聚合用户所有学习数据，返回报告所需的全部指标"""

    # 1. 学生画像
    profile_data = {}
    profile_scores = {}
    try:
        rows = query("SELECT profile_data FROM student_profiles WHERE user_id = %s", (user_id,))
        if rows:
            data = json.loads(rows[0]["profile_data"]) if isinstance(rows[0]["profile_data"], str) else rows[0]["profile_data"]
            dim_labels = {"knowledge_base": "知识基础", "learning_style": "学习风格", "weak_points": "学习难点",
                          "interests": "兴趣方向", "goals": "学习目标", "learning_pace": "学习节奏", "interaction_pref": "交互偏好"}
            for k, label in dim_labels.items():
                val = data.get(k, "")
                if isinstance(val, str) and val.strip():
                    profile_data[label] = val
            # 提取 visual 中的 radar_scores
            visual = data.get("__visual__", {})
            if isinstance(visual, dict):
                profile_scores = visual.get("radar_scores", {})
    except Exception as e:
        logger.error(f"获取画像失败: {e}")

    # 2. 会话统计
    profile_sessions = 0
    tutor_sessions = 0
    tutor_messages = 0
    try:
        rows = query(
            "SELECT session_type, messages FROM chat_sessions WHERE user_id = %s",
            (user_id,)
        )
        for r in rows:
            msgs = json.loads(r["messages"]) if isinstance(r["messages"], str) else r["messages"]
            if r["session_type"] == "profile_building":
                profile_sessions += 1
            elif r["session_type"] == "tutoring":
                tutor_sessions += 1
                tutor_messages += len(msgs)
    except Exception as e:
        logger.error(f"获取会话统计失败: {e}")

    # 3. 辅导问答统计（从tutoring session中提取）
    qa_count = 0
    modes_used = {}
    recent_questions = []
    try:
        rows = query(
            "SELECT messages FROM chat_sessions WHERE user_id = %s AND session_type = 'tutoring' ORDER BY updated_at DESC LIMIT 10",
            (user_id,)
        )
        for r in rows:
            msgs = json.loads(r["messages"]) if isinstance(r["messages"], str) else r["messages"]
            for m in msgs:
                if m.get("role") == "user":
                    qa_count += 1
                    mode = m.get("mode", "text")
                    modes_used[mode] = modes_used.get(mode, 0) + 1
                    if len(recent_questions) < 5:
                        recent_questions.append(m["content"][:60])
    except Exception:
        pass

    # 4. 维度评分（用于雷达图）
    dim_keys = ["知识基础", "学习风格", "学习难点", "兴趣方向", "学习目标", "学习节奏", "交互偏好"]
    radar_values = []
    for k in dim_keys:
        score = profile_scores.get(k, 0)
        radar_values.append(int(score) if score else 0)

    # 5. 学习活跃度（按日期统计session更新）
    activity = []
    try:
        rows = query(
            "SELECT DATE(updated_at) as day, COUNT(*) as cnt FROM chat_sessions WHERE user_id = %s GROUP BY DATE(updated_at) ORDER BY day DESC LIMIT 14",
            (user_id,)
        )
        activity = [{"date": str(r["day"]), "count": r["cnt"]} for r in rows]
    except Exception:
        pass

    return {
        "user_id": user_id,
        "has_profile": bool(profile_data),
        "profile": profile_data,
        "radar": {"labels": dim_keys, "values": radar_values},
        "stats": {
            "profile_sessions": profile_sessions,
            "tutor_sessions": tutor_sessions,
            "tutor_messages": tutor_messages,
            "qa_count": qa_count,
        },
        "modes_used": modes_used,
        "recent_questions": recent_questions,
        "activity": activity,
    }


@router.get("/ai-evaluation")
def get_ai_evaluation(user_id: int):
    """AI 生成学习评估报告"""

    # 先获取 summary 数据
    summary = get_report_summary(user_id)

    if not summary["has_profile"]:
        return {"evaluation": "请先完成学习画像构建，AI 才能为你生成评估报告。", "has_data": False}

    profile_text = "\n".join(f"- {k}: {v}" for k, v in summary["profile"].items())
    radar_text = "\n".join(f"- {l}: {v}/10" for l, v in zip(summary["radar"]["labels"], summary["radar"]["values"]) if v > 0)
    stats = summary["stats"]

    prompt = f"""你是学习评估专家。根据以下学生数据生成一份简洁的学习评估报告。

## 学生画像
{profile_text}

## 能力评分
{radar_text}

## 学习活跃度
- 画像构建会话: {stats['profile_sessions']} 次
- 辅导问答会话: {stats['tutor_sessions']} 次
- 辅导问答总数: {stats['qa_count']} 个问题
- 常用辅导模式: {json.dumps(summary['modes_used'], ensure_ascii=False)}

## 最近提问
{chr(10).join(f'- {q}' for q in summary['recent_questions']) if summary['recent_questions'] else '暂无'}

请输出以下内容（Markdown格式，不要代码块）：

### 总体评价
2-3句话概括学习状态

### 优势领域
列出2-3个突出的方面

### 需要加强
列出2-3个薄弱的方面

### 改进建议
3条具体可执行的建议

### 下一步行动
最推荐的1件事"""

    try:
        resp = chat_deepseek([{"role": "system", "content": prompt}], temperature=0.6, max_tokens=1500)
        evaluation = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI评估生成失败: {e}")
        evaluation = "AI 评估暂时不可用，请稍后再试。"

    return {"evaluation": evaluation, "has_data": True}
