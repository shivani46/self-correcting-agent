import re

import httpx
from groq import Groq

from executor import run_code
from prompts import SYSTEM_PROMPT, build_correction_prompt, build_generation_prompt

MAX_ATTEMPTS = 5

FAILURE_SIGNALS = {"403", "blocked", "error", "failed", "exception", "traceback"}


def looks_like_failure(stdout: str) -> bool:
    if not stdout.strip():
        return True
    lower = stdout.lower()
    return any(signal in lower for signal in FAILURE_SIGNALS)


def extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def run_agent(task: str) -> None:
    client = Groq(http_client=httpx.Client(verify=False))

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_generation_prompt(task)},
    ]

    all_errors: list[str] = []

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n{'=' * 52}")
        print(f"  Attempt {attempt} of {MAX_ATTEMPTS}")
        print(f"{'=' * 52}")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
        )
        raw_reply = response.choices[0].message.content
        code = extract_code(raw_reply)

        print(f"\nGenerated code:\n{'-' * 40}\n{code}\n{'-' * 40}")

        result = run_code(code)

        stdout_looks_bad = looks_like_failure(result["stdout"])
        if result["success"] and not stdout_looks_bad:
            print("\nOutput:")
            print(result["stdout"])
            print(f"\n[OK] Succeeded on attempt {attempt}.")
            return

        if result["success"] and stdout_looks_bad:
            error_detail = f"Code exited successfully but output indicates failure:\n{result['stdout'].strip()}"
        else:
            error_detail = result["stderr"].strip() or result["stdout"].strip() or "Non-zero exit code with no output."
        print(f"\nFailed:\n{error_detail}")

        all_errors.append(error_detail)

        if attempt < MAX_ATTEMPTS:
            print("\nFeeding error back to the model for correction...")
            messages.append({"role": "assistant", "content": raw_reply})
            messages.append({
                "role": "user",
                "content": build_correction_prompt(task, code, error_detail, attempt, all_errors),
            })

    print(f"\n{'=' * 52}")
    print(f"  Agent gave up after {MAX_ATTEMPTS} attempts.")
    print(f"{'=' * 52}")
