FROM python:3.11-slim
WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app + shared code
COPY main.py /app
# ⬇️ add this line for every agent
COPY ../../shared /app/shared

# (optional) make Python import from /app
ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
