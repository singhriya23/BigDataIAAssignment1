# Use a lightweight base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies needed for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files first to leverage Docker caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Now copy the rest of the application files
COPY . /app

# Expose the correct port
EXPOSE 8080

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
