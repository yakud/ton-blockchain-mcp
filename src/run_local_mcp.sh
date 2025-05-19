#!/bin/bash
export PYTHONPATH=$PWD/src
uvicorn tonmcp.mcp_server:app --reload --port 8000 