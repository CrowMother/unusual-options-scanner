# Base image with Python
FROM python:3.11-slim

# Set the timezone environment variable (adjust to your desired timezone)
ENV TZ=America/New_York

# Install tzdata and set the timezone
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Set the default command to run the script
CMD ["python", "main.py"]
