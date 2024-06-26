#!/bin/bash

# Evaluate and export environment variables
export WORKSPACE_BASE="~/Projects/VsCode/ai-exp/ai-experiments/ai-agents/use-cases/ai-swe/opendevin/workspace"
export SANDBOX_USER_ID=$(id -u)
export SSH_PASSWORD="make_something_up_here"
export DATE=$(date +%Y%m%d%H%M%S)

# Run Docker Compose
docker-compose up -d