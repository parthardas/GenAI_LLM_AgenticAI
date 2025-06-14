# === Stage 1: Build ReactJS Frontend ===
FROM node:20-alpine AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
RUN npm run build

# === Stage 2: Build FastAPI Backend ===
FROM python:3.10-slim AS backend

WORKDIR /app

# Copy backend files
COPY app.py ./
COPY guideline_agent.py ./
COPY account_agent.py ./
COPY billing_agent.py ./
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend build into FastAPI's static folder
COPY --from=frontend /app/frontend/dist ./static

# Allow CORS and serve static
ENV PYTHONUNBUFFERED=1

# === Use Uvicorn to launch app ===
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
