FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV WORKER_COUNT=4
CMD ["sh", "-c", "uvicorn services.episodic_memory.app:app --host 0.0.0.0 --port 8081 --workers ${WORKER_COUNT}"]
