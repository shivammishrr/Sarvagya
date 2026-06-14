from sarvagya.core.context import build_context, truncate_messages
from sarvagya.core.types import AgentResult, Message, ToolResult


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
            context = build_context(
                messages=truncate_messages(self._messages),
                tool_defs=self._tools.tool_defs(),
                workdir=self._workdir,
                iteration=i + 1,
                max_iterations=max_iterations,
                memory_index=self._get_memory_index(),
            )

            try:
                response = self._llm.complete(
                    messages=[
                        Message(
                            role=m["role"],
                            content=m.get("content", ""),
                            tool_call_id=m.get("tool_call_id"),
                            name=m.get("name"),
                        )
                        for m in context
                    ],
                    tools=self._tools.tool_defs(),
                )
            except Exception as e:
                return AgentResult(
                    success=False, output="", iterations=i + 1, error=str(e)
                )

            if response.tool_calls:
                for tc in response.tool_calls:
                    self._messages.append(
                        Message(role="assistant", content="", name=tc.name)
                    )
                    result: ToolResult = self._tools.execute(tc.name, tc.arguments)
                    self._messages.append(
                        Message(
                            role="tool",
                            content=result.output[:10000],
                            tool_call_id=tc.id,
                            name=tc.name,
                        )
                    )
            elif response.content:
                return AgentResult(
                    success=True,
                    output=response.content,
                    iterations=i + 1,
                )

        return AgentResult(
            success=False,
            output="",
            iterations=max_iterations,
            error="Max iterations reached without final answer",
        )

    def _get_memory_index(self) -> str:
        entries = self._memory.list()
        if not entries:
            return ""
        lines = ["## Memory"]
        for e in entries:
            lines.append(f"- {e.key}: {e.content[:80]}...")
        return "\n".join(lines)
