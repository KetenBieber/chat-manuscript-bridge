FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
RUN pip install --no-cache-dir .
ENV BRIDGE_TRANSPORT=http
EXPOSE 8000
USER 65532
CMD ["uvicorn", "chat_manuscript_bridge.server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
