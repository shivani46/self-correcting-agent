import sys

from agent import run_agent


def main() -> None:
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        print("Self-Correcting Code Agent")
        print("-" * 30)
        task = input("Enter a task: ").strip()
        if not task:
            print("No task provided. Exiting.")
            sys.exit(1)

    print(f"\nTask: {task}")
    run_agent(task)


if __name__ == "__main__":
    main()
