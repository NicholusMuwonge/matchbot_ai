#!/bin/bash

# Development script for hot reloading frontend in Docker

echo "🚀 Starting frontend development server with hot reloading..."
echo "📝 Files will automatically reload when you save changes"
echo "🌐 Frontend will be available at: http://localhost:5173"
echo "🔄 Press Ctrl+C to stop"
echo ""

# Start frontend service with file watching
cd /home/nick/matchbot_ai

# Use docker compose watch for optimal file syncing
docker compose --file docker-compose.yml --file docker-compose.override.yml up frontend --build --watch
