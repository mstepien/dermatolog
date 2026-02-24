#!/bin/bash
# Helper script to run tests inside the Docker container

echo "Running tests in the 'app' container..."
docker compose exec app pytest "$@"
