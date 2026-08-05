#!/data/data/com.termux/files/usr/bin/bash

# Sovereign Daemon Control Script for Termux
PID_FILE="$HOME/.sovereign_relayer.pid"
LOG_FILE="$HOME/sovereign_relayer.log"

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "[Sovereign Daemon]: Already running with PID $(cat $PID_FILE)"
    else
      echo "[Sovereign Daemon]: Starting ZK Relayer Daemon in background..."
      # Explicitly export NODE_PATH to resolve local node_modules
      export NODE_PATH="$HOME/node_modules"
      nohup npx tsx ZkRelayerDaemon.ts >> "$LOG_FILE" 2>&1 &
      echo $! > "$PID_FILE"
      echo "[Sovereign Daemon]: Started successfully (PID: $(cat $PID_FILE))"
    fi
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      echo "[Sovereign Daemon]: Stopping process PID $(cat $PID_FILE)..."
      kill $(cat "$PID_FILE") 2>/dev/null && rm -f "$PID_FILE"
      echo "[Sovereign Daemon]: Daemon stopped."
    else
      echo "[Sovereign Daemon]: No running PID file found."
    fi
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "[Sovereign Daemon]: RUNNING (PID: $(cat $PID_FILE))"
    else
      echo "[Sovereign Daemon]: STOPPED"
    fi
    ;;
  logs)
    tail -n 50 -f "$LOG_FILE"
    ;;
  *)
    echo "Usage: $0 {start|stop|status|logs}"
    exit 1
    ;;
esac
