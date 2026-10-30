# PlayIntel MCP server (hosted connector). Build context: backend/
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py mcp_server.py mcp_auth.py mcp_connect.html \
     alex_knowledge_base.txt indie_game_industry_knowledge.txt ./
ENV MCP_TRANSPORT=http PORT=8080 PYTHONUNBUFFERED=1
EXPOSE 8080
USER nobody
CMD ["python", "mcp_server.py"]
