# Single-image deploy: build the frontend, then serve it from FastAPI.
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend /app/frontend/dist ./frontend/dist
EXPOSE 8000
# Shell form so Railway/Render can inject $PORT; falls back to 8000 locally.
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
