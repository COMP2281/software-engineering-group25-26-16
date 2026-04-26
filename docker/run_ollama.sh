#!/bin/bash

echo "Starting Ollama server..."
ollama serve &  # Start Ollama in the background

# echo "Ollama is pulling the model..."
# ollama pull $GRANITE_MODEL

echo "Ollama is ready!"
wait
