FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Spark
RUN apt-get update && apt-get install -y openjdk-21-jre openjdk-21-jdk-headless && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run processor
CMD ["python", "processor.py"]

