import argparse
import os

from sarvagya.core import run


def main():
    parser = argparse.ArgumentParser(description="Sarvagya - Autonomous AI Agent")
    parser.add_argument("task", nargs="?", help="Task prompt for the agent")
    parser.add_argument("--workdir", default=os.getcwd())
    parser.add_argument("--provider", default="openai",
                        choices=["openai", "anthropic"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--max-iterations", type=int, default=50)

    args = parser.parse_args()
    task = args.task or os.environ.get("SARVAGYA_TASK")

    if not task:
        parser.print_help()
        print("\nError: task prompt is required")
        return

    result = run(task=task, workdir=args.workdir, provider=args.provider,
                 model=args.model, api_key=args.api_key,
                 max_iterations=args.max_iterations)

    if result.error:
        print(f"Error: {result.error}")
    if result.output:
        print(result.output)


if __name__ == "__main__":
    main()
