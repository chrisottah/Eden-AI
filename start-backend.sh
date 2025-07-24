#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/workspace/Eden-AI/backend
uvicorn open_webui.main:app --host 0.0.0.0 --port 8081 --reload
