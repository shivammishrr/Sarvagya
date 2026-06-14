from sarvagya.core.context import build_context, truncate_messages
from sarvagya.core.types import AgentResult, LLMResponse, Message, ToolCall, ToolResult

MAX_OUTPUT_LEN = 10_000
MAX_MEMORY_PREVIEW = 80


class AgentLoop:
    def __init__(self, llm, sandbox, memory, tools, workdir: str):
        self._llm = llm
        self._sandbox = sandbox
        self._memory = memory
        self._tools = tools
        self._workdir = workdir
        self._messages: list[Message] = []

    def run(self, task: str, max_iterations: int = 50) -> AgentResult:
        self._messages.append(Message(role="user", content=task))
        for i in range(max_iterations):
            result = self._step(i, max_iterations)
            if result is not None:
                return result
        return AgentResult(
            success=False, output="", iterations=max_iterations,
            error="Max iterations reached without final answer",
        )

    def _step(self, iteration: int, max_iterations: int) -> AgentResult | None:
        context = build_context(
            messages=truncate_messages(self._messages),
            tool_defs=self._tools.tool_defs(),
            workdir=self._workdir,
            iteration=iteration + 1,
            max_iterations=max_iterations,
            memory_index=self._get_memory_index(),
        )
        response = self._call_llm(context)
        if isinstance(response, AgentResult):
            return response
        return self._handle_response(response, iteration)

    def _call_llm(self, context: list[dict]) -> LLMResponse | AgentResult:
        try:
            msgs: list[Message] = []
            for m in context:
                kwargs = {"role": m["role"], "content": m.get("content", ""),
                          "tool_call_id": m.get("tool_call_id"), "name": m.get("name")}
                if "tool_calls" in m:
                    kwargs["tool_calls"] = [ToolCall(id=tc["id"], name=tc["function"]["name"], arguments=tc["function"]["arguments"]) for tc in m["tool_calls"]]
                msgs.append(Message(**kwargs))
            return self._llm.complete(messages=msgs, tools=self._tools.tool_defs())
        except Exception as e:
            return AgentResult(success=False, output="", error=str(e))

    def _handle_response(self, response: LLMResponse, iteration: int) -> AgentResult | None:
        if response.tool_calls:
            self._messages.append(Message(role="assistant", content=response.content or "", tool_calls=response.tool_calls))
            for tc in response.tool_calls:
                result: ToolResult = self._tools.execute(tc.name, tc.arguments)
                self._messages.append(Message(
                    role="tool", content=result.output[:MAX_OUTPUT_LEN],
                    tool_call_id=tc.id, name=tc.name,
                ))
            return None
        if response.content:
            return AgentResult(success=True, output=response.content, iterations=iteration + 1)
        return None

    def _get_memory_index(self) -> str:
        entries = self._memory.list()
        if not entries:
            return ""
        lines = ["## Memory"]
        for e in entries:
            lines.append(f"- {e.key}: {e.content[:MAX_MEMORY_PREVIEW]}...")
        return "\n".join(lines)
