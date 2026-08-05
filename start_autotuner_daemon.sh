#!/usr/bin/env bash

AUTOTUNER_BIN="$HOME/autotuner"
LOG_FILE="$HOME/autotuner.log"

if [ ! -f "$AUTOTUNER_BIN" ]; then
    echo "❌ Binary not found at $AUTOTUNER_BIN. Compile main.cpp first."
    exit 1
fi

echo "⚡ Starting Autotuner Daemon in background..."
nohup "$AUTOTUNER_BIN" >> "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$HOME/autotuner.pid"

echo "✅ Autotuner PID: $PID"
echo "📄 Tracking live logs at $LOG_FILE"
