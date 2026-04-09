# TerminalBrain - Day 10

Your terminal but smarter. Wraps any command, catches errors live, asks local AI for the fix — without stopping your output.

## How to run
Make sure ollama is running first:
ollama serve

Then wrap any command:
python day10_starter.py python -c "import nonexistent"
python day10_starter.py python your_script.py

## What it does
Runs your command normally.
Watches stderr in real time on a separate thread.
When it spots an error, sends it to qwen2.5:3b locally.
Prints the fix suggestion in cyan without interrupting anything.
Caches fixes so repeated errors are instant.

## Hardware concept
Hardware watchdog timers monitor system state and trigger recovery when something fails.
TerminalBrain is the software version — the wrapper is the watchdog, the LLM is the recovery handler.

## Tech stack
ollama + qwen2.5:3b, subprocess PIPE, threading, queue

## Common fixes
ollama not running → ollama serve
model missing → ollama pull qwen2.5:3b
Brain times out → close other apps, free up RAM

Built for Day 10 of Build Core'd Orcas 🐋
