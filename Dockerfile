# Use Ubuntu as base image for good package support
FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set environment variables for paths (can be overridden at runtime)
ENV WATCH_DIR=/app/data/input
ENV WORK_DIR=/app/data/working
ENV FINAL_DIR=/app/data/output
ENV DEBUG_DIR=/app/data/debug
ENV DB_PATH=/app/data/documents.db

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY *.py ./
COPY templates/ ./templates/

# Create data directories with proper permissions
RUN mkdir -p ${WATCH_DIR} ${WORK_DIR} ${FINAL_DIR} ${DEBUG_DIR} && \
    chmod 755 ${WATCH_DIR} ${WORK_DIR} ${FINAL_DIR} ${DEBUG_DIR}

# Expose port for web interface
EXPOSE 5000

# Create entrypoint script to handle both batch and web modes
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command (web interface)
CMD ["web"]