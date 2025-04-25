# Use the official Python 3.10 base image
FROM python:3.13.3-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED: Ensures that the Python output is sent straight to the terminal (unbuffered)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python packages
COPY requirements.txt /app/

RUN pip3 install --no-cache-dir -r requirements.txt

# Copy mapping folder to the working directory
COPY . /app/

# Create a non-root user and group
RUN groupadd -g 1000 cpuadupdater && \
    useradd -u 1000 -g cpuadupdater -s /bin/bash -m cpuadupdater

# Change ownership of the directories
RUN chown -R cpuadupdater:cpuadupdater /app

# Switch to the new user
USER cpuadupdater

# Run the command one time
CMD ["python3", "update_grafana.py"]
