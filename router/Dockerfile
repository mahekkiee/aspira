FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and shared modules
COPY ../shared /app/shared
ENV PYTHONPATH=/app


# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
