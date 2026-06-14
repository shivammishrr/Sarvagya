from sarvagya.core.context import (
    build_dynamic_section,
    build_system_prompt,
    build_tool_section,
    format_messages,
    truncate_messages,
)
from sarvagya.core.types import (
    AgentResult,
    LLMResponse,
    Message,
    ToolCall,
    ToolResult,
)
from sarvagya.ports.llm import LLMProvider
from sarvagya.ports.memory import Memory
from sarvagya.ports.sandbox import Sandbox


class AgentLoop:
    def __init__(
        self,
        llm: LLMProvider,
        sandbox: Sandbox,
        memory: Memory,
        tools,
        workdir: str,
    ):
        self._llm = llm
        self._sandbox = sandbox
        self._memory = memory
        self._tools = tools
        self._workdir = workdir
        self._messages: list[Message] = []
        self._system_prompt = build_system_prompt()

    def run(
        self,
        task: str,
        max_iterations: int = 50,
    ) -> AgentResult:
        self._messages.append(Message(role="user", content=task))

        for iteration in range(max_iterations):
            dynamic = build_dynamic_section(
                workdir=self._workdir,
                memory_index=self._get_memory_index(),
                iteration=iteration + 1,
                max_iterations=max_iterations,
            )
            tool_section = build_tool_section(self._tools.tool_defs())
            formatted = format_messages(
                messages=truncate_messages(self._messages),
                system_prompt=self._system_prompt,
                dynamic_section=dynamic,
                tool_section=tool_section,
                schemas=self._tools.schemas(),
            )

            try:
                response: LLMResponse = self._llm.complete(
                    messages=[
                        Message(
                            role=m["role"],
                            content=m.get("content", ""),
                            tool_call_id=m.get("tool_call_id"),
                            name=m.get("name"),
                        )
                        for m in formatted
                    ],
                    tools=self._tools.tool_defs(),
                )
            except Exception as e:
                return AgentResult(
                    success=False,
                    output="",
                    iterations=iteration + 1,
                    error=str(e),
                )

            if response.tool_calls:
                for tc in response.tool_calls:
                    self._messages.append(
                        Message(
                            role="assistant",
                            content="",
                            name=tc.name,
                        )
                    )
                    result: ToolResult = self._tools.execute(
                        tc.name, tc.arguments
                    )
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
                    iterations=iteration + 1,
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
