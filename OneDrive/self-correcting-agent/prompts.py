SYSTEM_PROMPT = """You are an expert Python programmer. Your job is to write clean, correct, runnable Python code.

Rules:
- Output ONLY a Python code block, nothing else before or after it
- The code must be complete and runnable as a standalone script
- Use only the Python standard library unless the task explicitly requires external packages
- Always print your results so the output is visible
- Format your response exactly as:
```python
# your code here
```
"""


def build_generation_prompt(task: str) -> str:
    return f"Write Python code to complete the following task:\n\n{task}"


def build_correction_prompt(task: str, code: str, error: str, attempt: int, all_errors: list[str] | None = None) -> str:
    history = ""
    if all_errors and len(all_errors) > 1:
        lines = "\n".join(f"  Attempt {i + 1}: {e}" for i, e in enumerate(all_errors[:-1]))
        history = f"Errors from all previous attempts (do NOT repeat any of these mistakes):\n{lines}\n\n"
    return (
        f"The code you wrote failed on attempt {attempt}.\n\n"
        f"Original task:\n{task}\n\n"
        f"{history}"
        f"Code that just failed:\n```python\n{code}\n```\n\n"
        f"Latest error:\n{error}\n\n"
        "Write a corrected version that fixes ALL of the above errors at once. "
        "Output ONLY the corrected Python code block."
    )
