#!/bin/bash

# Quit if a command exits with a non-zero status
set -e

# Start Ollama in background
ollama serve &

# Wait until API is ready
until curl -s http://localhost:11434 >/dev/null; do
  echo "Waiting for Ollama..."
  sleep 2
done

echo "Ollama is ready"

# Pull model (only if missing)
ollama pull llama3.1:8b

echo "Model ready"

# Keep script running to keep Ollama alive
wait