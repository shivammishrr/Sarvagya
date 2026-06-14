export default async ({ client, project, directory, $ }) => {
  return {
    "experimental.chat.system.transform": async (input) => {
      const pony = `

## Ponytail Philosophy - Write Bug-Free Minimal Code

### Delete Before You Write
- Can this be solved with existing code? If yes, don't write new code.
- Is this feature actually necessary? If not, delete the idea.
- What happens if I don't write this? If nothing bad, don't write it.

### YAGNI (You Aren't Gonna Need It)
- Three Strikes Rule: don't abstract until the 3rd duplication.
- No speculative features. Build what is needed NOW.
- Every abstraction has a cost. Don't pay it for hypotheticals.

### Staircase Pattern
1. Can I solve this with a library?
2. Can I solve this with existing functions?
3. Can I solve this with simpler code?
4. Now I can write new code.

### Single Responsibility
- One reason to change per function/class.
- God functions (>30 lines) are banned. Split them.
- If a class has two unrelated responsibilities, split it.

### Explicit Over Clever
- Clear > Short. Obvious > Elegant. Boring > Smart.
- Name variables after meaning, not mechanics.
- No magic numbers. No "just trust me" logic.
- Split complex expressions into named steps.

### Boundary Validation
- Validate type, range, format at entry points only.
- Fail fast with clear error messages.
- Don't spread validation everywhere.

### Error Handling
- Every external call must have a timeout.
- Every operation must handle failure explicitly.
- Errors are structured data, not strings.
- No silent failures. No empty catch blocks.

### No Wasteful Comments
- Code is self-documenting through structure, not comments.
- Comments explain WHY, not WHAT or HOW.
- No commented-out code. Delete it.
- No TODO comments without owning context.

### Output Minimalism
- No emojis. No status messages. Short direct answers.
- Default to the smallest possible output.
- One action per iteration where possible.

### Framework Agnostic
- Core domain imports ZERO external packages.
- All external dependencies live behind ports (Protocols).
- Adapters translate between domain types and SDK formats.
- Configuration determines which adapter to use, not code.
`
      return {
        messages: input.messages,
        system: input.system + pony,
      }
    },
    "tool.execute.after": async (input, output) => {
      const result = output?.result?.output || ""
      if (!result) return

      const flags = []

      if (result.includes("TODO") || result.includes("FIXME") || result.includes("HACK")) {
        flags.push("⚠️  Contains TODO/FIXME/HACK markers")
      }
      if (result.includes("except:\n        pass") || result.includes("except Exception as e:\n        pass")) {
        flags.push("❌ Empty except block detected")
      }
      if (result.includes("raise Exception")) {
        flags.push("⚠️  Uses generic Exception - use specific error types")
      }
      if (result.includes("import *")) {
        flags.push("❌ Wildcard import detected")
      }

      if (flags.length > 0 && typeof output === "object" && output !== null) {
        output.warnings = (output.warnings || []).concat(flags)
      }
    },
  }
}
