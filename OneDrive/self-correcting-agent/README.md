# Self-Correcting Code Agent

A Python agent that writes code to solve a task, executes it, and automatically corrects itself when the code fails — up to a configurable number of attempts. It uses [Groq](https://groq.com) with **Llama 3.3 70B** as the LLM backbone.

## Demo

Running the agent on a real-world web scraping task:

```
python main.py "write a web scraper that fetches the title and first paragraph from https://en.wikipedia.org/wiki/Python_(programming_language) and prints them"
```

The agent self-corrected across 4 attempts before succeeding:

| Attempt | Outcome | What went wrong | What the model fixed |
|---------|---------|-----------------|----------------------|
| 1 | Fail | `ModuleNotFoundError: No module named 'bs4'` | Dropped BeautifulSoup; rewrote with stdlib `html.parser` |
| 2 | Fail | `SSL: CERTIFICATE_VERIFY_FAILED` | Added `verify=False` to `requests.get()` |
| 3 | Fail | HTTP 403 Forbidden (Wikipedia blocked the bot) | Cumulative error history told it to fix *all* past errors at once — added `User-Agent` header while keeping `verify=False` |
| 4 | **Pass** | — | Combined: stdlib parser + `verify=False` + browser `User-Agent` |

Final output:

```
Title: Python (programming language)
First Paragraph: Python is a high-level, general-purpose programming language that
emphasizes code readability, simplicity, and ease-of-writing...
```

## Architecture

```
main.py
  └── run_agent(task)          # agent.py
        ├── build_generation_prompt()   # prompts.py
        ├── Groq API call (llama-3.3-70b-versatile)
        ├── extract_code()
        ├── run_code()          # executor.py  ← subprocess in a temp file
        ├── looks_like_failure()   # semantic stdout check
        └── build_correction_prompt(all_errors)  # prompts.py
```

### Files

| File | Role |
|------|------|
| `main.py` | Entry point — reads the task from CLI args or prompts the user |
| `agent.py` | Core loop — calls the LLM, extracts code, evaluates output, retries |
| `executor.py` | Runs a code string in a subprocess; returns `{success, stdout, stderr, exit_code}` |
| `prompts.py` | System prompt, generation prompt, and cumulative correction prompt |

## The Reflection Loop

```
┌─────────────────────────────────────────────┐
│                  run_agent                  │
│                                             │
│  for attempt in 1..MAX_ATTEMPTS:            │
│    1. Call LLM → raw reply                  │
│    2. Extract Python code block             │
│    3. Run code in subprocess                │
│    4. Evaluate:                             │
│       - exit code != 0  → fail             │
│       - stdout empty    → fail             │
│       - stdout contains "error", "403",    │
│         "failed", etc.  → fail             │
│       - otherwise       → SUCCESS, return  │
│    5. Append error to all_errors[]          │
│    6. Build correction prompt with the full │
│       history of all past errors            │
│    7. Append assistant + user turns to      │
│       the conversation and loop             │
└─────────────────────────────────────────────┘
```

The key insight is the **cumulative error history**: each correction prompt includes a summary of every failure so far, not just the most recent one. This prevents the model from fixing one problem while re-introducing a previously solved one.

## Setup

```bash
pip install groq httpx
```

Set your Groq API key (free at [console.groq.com](https://console.groq.com)):

```bash
export GROQ_API_KEY="gsk_..."   # Linux/macOS
$env:GROQ_API_KEY="gsk_..."     # Windows PowerShell
```

## Usage

```bash
python main.py "find all prime numbers up to 100 and print them"
python main.py "write a web scraper that fetches the title and first paragraph from https://en.wikipedia.org/wiki/Python_(programming_language) and prints them"
```

Or run without arguments to be prompted:

```bash
python main.py
```

## Configuration

| Variable | Location | Default | Description |
|----------|----------|---------|-------------|
| `MAX_ATTEMPTS` | `agent.py` | `5` | Maximum retry attempts |
| `FAILURE_SIGNALS` | `agent.py` | `{"403", "blocked", "error", ...}` | Words in stdout that signal a silent failure |
| `model` | `agent.py` | `llama-3.3-70b-versatile` | Groq model to use |
| `temperature` | `agent.py` | `0.2` | LLM temperature |
