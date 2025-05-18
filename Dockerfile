FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/src

COPY . .

CMD ["uvicorn", "src.tonmcp.mcp_server:app", "--host", "0.0.0.0", "--port", "8000"] 