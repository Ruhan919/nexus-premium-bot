#!/bin/bash
# Start both health server and bot
python web_server.py &
python nexus_bot.py
