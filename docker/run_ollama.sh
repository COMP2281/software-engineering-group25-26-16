#!/bin/bash

echo "Starting Ollama server..."
ollama serve &  # Start Ollama in the background

sleep 5

echo "Ollama is pulling the model..."
ollama pull granite4:350m

echo "Ollama is ready!"
wait
