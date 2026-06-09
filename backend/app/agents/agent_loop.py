"""
Agent Loop — FastGPT-style Plan-then-Execute Agent
LLM 自主决定调用哪些工具，循环执行直到 Stop Gate 通过
"""
import json
import time
from typing import Callable, Any
from app.services.llm import chat_deepseek, chat_qwen


# ─── Tool Registry ───────────────────────────────────────

class Tool:
    def __init__(self, name: str, description: str, parameters: dict, handler: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": list(self.parameters.keys()),
                },
            },
        }

    def execute(self, args: dict) -> str:
        return self.handler(args)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def execute(self, name: str, args: dict) -> str:
        if name not in self._tools:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            return self._tools[name].execute(args)
        except Exception as e:
            return json.dumps({"error": str(e)})


# ─── Planner ────────────────────────────────────────────

class Planner:
    """管理执行计划"""
    def __init__(self):
        self.steps: list[dict] = []
        self.current_step = 0

    def set_plan(self, steps: list[str]):
        self.steps = [{"id": i, "title": s, "status": "pending"} for i, s in enumerate(steps)]
        self.current_step = 0

    def mark_done(self, step_id: int):
        if step_id < len(self.steps):
            self.steps[step_id]["status"] = "done"

    def mark_blocked(self, step_id: int, reason: str):
        if step_id < len(self.steps):
            self.steps[step_id]["status"] = "blocked"
            self.steps[step_id]["blocker"] = reason

    def is_complete(self) -> bool:
        if not self.steps:
            return True
        return all(s["status"] in ("done", "skipped", "blocked") for s in self.steps)

    def pending_count(self) -> int:
        return sum(1 for s in self.steps if s["status"] == "pending")

    def summary(self) -> str:
        if not self.steps:
            return "无计划"
        lines = [f"{s['id']}. [{s['status']}] {s['title']}" for s in self.steps]
        return "\n".join(lines)


# ─── Stop Gate ──────────────────────────────────────────

def run_stop_gate(planner: Planner, tool_called_this_round: bool, asked_user: bool = False) -> tuple[bool, str]:
    """检查是否可以停止执行。如果刚问了用户问题（等待回复中），允许停止"""
    if asked_user:
        return True, "Waiting for user response"
    if planner.is_complete():
        return True, "Plan complete"
    pending = planner.pending_count()
    if pending > 0:
        return False, f"还有 {pending} 个步骤未完成，请继续执行。但如果你是刚刚问了学生一个问题在等待回复，可以忽略此提示"
    return True, "OK"


# ─── Agent Loop ─────────────────────────────────────────

def run_agent_loop(
    user_message: str,
    system_prompt: str,
    registry: ToolRegistry,
    planner: Planner,
    on_event: Callable[[str, Any], None] = None,
    max_rounds: int = 10,
) -> dict:
    """主 Agent 循环"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    tools = registry.get_schemas()
    tool_names = list(registry._tools.keys())
    all_results = []
    rounds = 0
    asked_user = False  # 标记是否向用户提问了

    while rounds < max_rounds:
        rounds += 1
        on_event and on_event("loop_start", {"round": rounds})

        # 调用 LLM（带工具）
        resp = chat_deepseek(
            messages=messages,
            temperature=0.3 if rounds > 1 else 0.7,
            max_tokens=2048,
            tools=tools if tools else None,
        )

        choice = resp.choices[0]
        msg = choice.message
        content = msg.content or ""
        tool_calls = getattr(msg, "tool_calls", None) or []

        # 非流式先解析 tool_calls
        parsed_calls = []
        if tool_calls:
            for tc in tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                parsed_calls.append({"id": tc.id, "name": tc.function.name, "args": args})

        on_event and on_event("llm_response", {
            "content": content[:200] if content else "",
            "tool_calls": [c["name"] for c in parsed_calls],
            "round": rounds,
        })

        # 如果没有工具调用 → LLM 想直接回答
        if not parsed_calls:
            # 如果刚问了用户问题 → 允许停止等待回复
            if asked_user:
                on_event and on_event("answer", {"text": content, "rounds": rounds, "waiting": True})
                return {"status": "waiting", "answer": content, "rounds": rounds}

            # Stop Gate 只做宽松检查
            can_stop, reason = run_stop_gate(planner, False, asked_user)
            if can_stop:
                on_event and on_event("answer", {"text": content, "rounds": rounds})
                return {"status": "done", "answer": content, "rounds": rounds, "plan_summary": planner.summary()}

            # Plan incomplete → gentle reminder
            on_event and on_event("stop_gate_reject", {"reason": reason})
            messages.append({"role": "assistant", "content": content})
            if rounds < 3:  # Only push back a few times
                messages.append({"role": "user", "content": f"[提示] {reason}"})
            else:
                # After 3 rounds, just accept and return
                on_event and on_event("answer", {"text": content, "rounds": rounds, "forced": True})
                return {"status": "done", "answer": content, "rounds": rounds}
            continue

        # 执行工具
        assistant_msg = {"role": "assistant", "content": content}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        for call in parsed_calls:
            on_event and on_event("tool_call", {"name": call["name"], "args": call["args"]})
            result = registry.execute(call["name"], call["args"])
            on_event and on_event("tool_result", {
                "name": call["name"],
                "result": result[:300],
            })
            # 检测 ask_dimension 工具 → 标记已向用户提问
            if call["name"] == "ask_dimension":
                asked_user = True
            all_results.append({"tool": call["name"], "args": call["args"], "result": result})
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result,
            })

        # 更新计划状态
        tool_called_this_round = len(parsed_calls) > 0
        if tool_called_this_round and not planner.is_complete():
            # 把当前步骤标记为完成
            planner.mark_done(planner.current_step)
            planner.current_step += 1

    # 达到最大轮数
    on_event and on_event("max_rounds", {"rounds": max_rounds})
    return {
        "status": "max_rounds",
        "answer": "抱歉，任务比较复杂，目前已完成部分工作。",
        "rounds": max_rounds,
        "results": all_results,
        "plan_summary": planner.summary(),
    }
