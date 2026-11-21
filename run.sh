#!/usr/bin/env bash
# Helper script for Instagram Reels Bot
cd "$(dirname "$0")"

case "$1" in
  login)
    .venv/bin/python uploader.py --login
    ;;
  sessionid)
    .venv/bin/python uploader.py --sessionid "$2"
    ;;
  post-now)
    .venv/bin/python uploader.py --post-now
    ;;
  status)
    .venv/bin/python uploader.py --status
    ;;
  start)
    echo "Starting Reels Bot scheduler in background..."
    nohup .venv/bin/python uploader.py --run > logs/bot.out 2>&1 &
    echo "Bot started! PID: $!"
    echo "Check logs with: tail -f logs/uploader.log"
    ;;
  stop)
    pkill -f "uploader.py --run" && echo "Bot stopped." || echo "No running bot process found."
    ;;
  *)
    .venv/bin/python uploader.py --status
    echo ""
    echo "Usage: ./run.sh [login|status|post-now|start|stop]"
    ;;
esac
