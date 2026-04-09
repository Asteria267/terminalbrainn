import os
os.system("")
import sys
import subprocess
import threading
import queue
import time

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────

MODEL = "qwen2.5:3b"

ERROR_PATTERNS = [
    "Traceback",
    "Error:",
    "Exception:",
    "ModuleNotFoundError",
    "ImportError",
    "NameError",
    "SyntaxError",
    "TypeError",
    "ValueError",
    "KeyError",
    "AttributeError",
    "FileNotFoundError",
    "FAILED",
    "FATAL",
]

fix_cache = {}

# ─────────────────────────────────────────────
#  COLORS
# ─────────────────────────────────────────────

RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
DIM    = "\033[2m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def is_error_line(line):
    return any(p in line for p in ERROR_PATTERNS)


def ask_ai(error_text):
    cache_key = error_text[:100].strip()
    if cache_key in fix_cache:
        print(f"\n{CYAN}Brain (cached): {fix_cache[cache_key]}{RESET}\n")
        return

    print(f"\n{CYAN}MY BrainN analyzing...{RESET}", flush=True)

    prompt = (
        "You are a terminal expert. Fix this error in one sentence. "
        "If it needs pip install, give the exact command. "
        "Be direct. No greetings.\n\nError:\n" + error_text
    )

    try:
        result = subprocess.run(
            ["ollama", "run", MODEL, prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        fix = result.stdout.strip()
        if fix:
            print(f"{CYAN}Brain: {fix}{RESET}\n")
            fix_cache[cache_key] = fix
        else:
            print(f"{YELLOW}Brain: no suggestion{RESET}\n")
    except subprocess.TimeoutExpired:
        print(f"{YELLOW}Brain: timed out (close other apps and retry){RESET}\n")
    except Exception as e:
        print(f"{YELLOW}Brain error: {e}{RESET}\n")


def read_stream(stream, output_queue, name):
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            output_queue.put((name, line))
    finally:
        stream.close()

# ─────────────────────────────────────────────
#  MAIN WRAPPER
# ─────────────────────────────────────────────

def run_with_brain(command):
    print(f"\n{CYAN}{BOLD}TerminalBrain{RESET} wrapping: {BOLD}{' '.join(command)}{RESET}")
    print(f"{DIM}" + "-" * 50 + f"{RESET}\n")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    except FileNotFoundError:
        print(f"{RED}Command not found: {command[0]}{RESET}")
        return
    except Exception as e:
        print(f"{RED}Failed to start: {e}{RESET}")
        return

    output_queue = queue.Queue()

    t_out = threading.Thread(
        target=read_stream,
        args=(process.stdout, output_queue, "stdout"),
        daemon=True
    )
    t_err = threading.Thread(
        target=read_stream,
        args=(process.stderr, output_queue, "stderr"),
        daemon=True
    )
    t_out.start()
    t_err.start()

    error_buffer = []
    in_error = False

    while True:
        try:
            name, line = output_queue.get(timeout=0.1)
            line = line.rstrip()

            if name == "stdout":
                print(f"{WHITE}{line}{RESET}")
                if in_error and error_buffer:
                    ask_ai("\n".join(error_buffer))
                    error_buffer = []
                    in_error = False

            elif name == "stderr":
                print(f"{RED}{line}{RESET}")
                if is_error_line(line):
                    in_error = True
                if in_error:
                    error_buffer.append(line)

        except queue.Empty:
            if process.poll() is not None:
                break

    if error_buffer:
        ask_ai("\n".join(error_buffer))

    process.wait()
    code = process.returncode

    if code == 0:
        print(f"\n{GREEN}Done. No errors.{RESET}\n")
    else:
        print(f"\n{DIM}Exit code: {code}{RESET}\n")

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(f"\nUsage: python terminal_brain.py <command>")
        print(f"Example: python terminal_brain.py python -c \"import nonexistent\"\n")
        return

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            print(f"{RED}Ollama not running. Start: ollama serve{RESET}")
            return
    except Exception:
        print(f"{RED}Ollama not found. Start: ollama serve{RESET}")
        return

    run_with_brain(sys.argv[1:])


if __name__ == "__main__":
    main()
