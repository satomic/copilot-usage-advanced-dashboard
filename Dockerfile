# Use the official Ubuntu 20.04 base image
FROM ubuntu:22.04

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# PYTHONUNBUFFERED: Ensures that the Python output is sent straight to the terminal (unbuffered)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python packages
COPY requirements.txt /app/

# if you are in China, use this command to speed up the installation
# RUN pip3 install -i https://mirrors.cloud.tencent.com/pypi/simple --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy mapping folder to the working directory
COPY mapping /app/mapping

# Copy the scripts to the working directory
COPY log_utils.py /app/
COPY main.py /app/
COPY metrics_2_usage_convertor.py /app/
COPY version /app/

# Run the command one time
CMD ["python3", "main.py"]
