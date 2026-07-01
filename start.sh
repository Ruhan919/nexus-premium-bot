#!/bin/bash
set -e
echo "Starting NEXUS Bot v5.0..."
echo "Starting web server for health check..."
python web_server.py &
WEB_PID=$!
echo "Web server PID: $WEB_PID"
sleep 2
echo "Starting Telegram bot..."
python nexus_bot.py
