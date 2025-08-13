# Docker Support for PDF Magic Monkey

This document provides step-by-step instructions for running PDF Magic Monkey in Docker containers on Kubuntu and other Linux systems.

## Overview

PDF Magic Monkey can be run in Docker containers in two modes:
- **Web Interface**: Access the document review interface via a web browser
- **Batch Processing**: Automatic processing of files placed in a watched directory

## Prerequisites

### Installing Docker on Kubuntu

1. **Update package index:**
   ```bash
   sudo apt update
   ```

2. **Install required packages:**
   ```bash
   sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release
   ```

3. **Add Docker's GPG key:**
   ```bash
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   ```

4. **Add Docker repository:**
   ```bash
   echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```

5. **Install Docker:**
   ```bash
   sudo apt update
   sudo apt install docker-ce docker-ce-cli containerd.io
   ```

6. **Add your user to the docker group (optional, to run without sudo):**
   ```bash
   sudo usermod -aG docker $USER
   ```
   Log out and back in for this to take effect.

## Building the Docker Image

1. **Clone the repository:**
   ```bash
   git clone https://github.com/assimilateDave/pdf-magic-monkey.git
   cd pdf-magic-monkey
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t pdf-magic-monkey .
   ```

## Directory Structure and Mounting

The application uses the following directories that should be mounted from the host for persistence:

### Container Directories

- `/app/data/input` - Input directory for new documents (batch mode)
- `/app/data/working` - Temporary processing directory
- `/app/data/output` - Final storage for processed documents  
- `/app/data/debug` - Debug images from preprocessing steps
- `/app/data/documents.db` - SQLite database file

### Host Directory Setup

Create directories on your host system:

```bash
mkdir -p ~/pdf-processing/{input,working,output,debug}
```

## Running the Containers

### Web Interface Mode

Run the web interface to review processed documents:

```bash
docker run -d \
  --name pdf-magic-web \
  -p 5000:5000 \
  -v ~/pdf-processing/input:/app/data/input \
  -v ~/pdf-processing/working:/app/data/working \
  -v ~/pdf-processing/output:/app/data/output \
  -v ~/pdf-processing/debug:/app/data/debug \
  -v ~/pdf-processing/documents.db:/app/data/documents.db \
  pdf-magic-monkey web
```

Access the web interface at: http://localhost:5000

### Batch Processing Mode

Run batch processing to automatically process files:

```bash
docker run -d \
  --name pdf-magic-batch \
  -v ~/pdf-processing/input:/app/data/input \
  -v ~/pdf-processing/working:/app/data/working \
  -v ~/pdf-processing/output:/app/data/output \
  -v ~/pdf-processing/debug:/app/data/debug \
  -v ~/pdf-processing/documents.db:/app/data/documents.db \
  pdf-magic-monkey batch
```

### Running Both Modes Simultaneously

You can run both the web interface and batch processing at the same time by using different container names and sharing the same mounted volumes:

1. **Start batch processing:**
   ```bash
   docker run -d \
     --name pdf-magic-batch \
     -v ~/pdf-processing/input:/app/data/input \
     -v ~/pdf-processing/working:/app/data/working \
     -v ~/pdf-processing/output:/app/data/output \
     -v ~/pdf-processing/debug:/app/data/debug \
     -v ~/pdf-processing/documents.db:/app/data/documents.db \
     pdf-magic-monkey batch
   ```

2. **Start web interface:**
   ```bash
   docker run -d \
     --name pdf-magic-web \
     -p 5000:5000 \
     -v ~/pdf-processing/input:/app/data/input \
     -v ~/pdf-processing/working:/app/data/working \
     -v ~/pdf-processing/output:/app/data/output \
     -v ~/pdf-processing/debug:/app/data/debug \
     -v ~/pdf-processing/documents.db:/app/data/documents.db \
     pdf-magic-monkey web
   ```

## Configuration Options

You can customize the application behavior using environment variables:

### Environment Variables

- `WATCH_DIR` - Input directory (default: `/app/data/input`)
- `WORK_DIR` - Working directory (default: `/app/data/working`)
- `FINAL_DIR` - Output directory (default: `/app/data/output`)
- `DEBUG_DIR` - Debug images directory (default: `/app/data/debug`)
- `DB_PATH` - Database file path (default: `/app/data/documents.db`)
- `TESSERACT_CMD` - Tesseract command (default: system tesseract)
- `POPPLER_PATH` - Poppler utilities path (default: system poppler)

### Custom Configuration Example

```bash
docker run -d \
  --name pdf-magic-batch \
  -e DEBUG_DIR=/app/data/custom-debug \
  -v ~/pdf-processing/input:/app/data/input \
  -v ~/pdf-processing/working:/app/data/working \
  -v ~/pdf-processing/output:/app/data/output \
  -v ~/pdf-processing/custom-debug:/app/data/custom-debug \
  -v ~/pdf-processing/documents.db:/app/data/documents.db \
  pdf-magic-monkey batch
```

## Mounting Configuration Files

If you need to mount custom configuration files, you can add additional volume mounts:

```bash
docker run -d \
  --name pdf-magic-web \
  -p 5000:5000 \
  -v ~/pdf-processing/input:/app/data/input \
  -v ~/pdf-processing/output:/app/data/output \
  -v ~/pdf-processing/debug:/app/data/debug \
  -v ~/pdf-processing/documents.db:/app/data/documents.db \
  -v ~/my-configs/custom.conf:/app/custom.conf \
  pdf-magic-monkey web
```

## File Processing Workflow

### Adding Files for Processing

1. **Place files in the input directory:**
   ```bash
   cp your-document.pdf ~/pdf-processing/input/
   ```

2. **The batch processor will automatically:**
   - Detect the new file
   - Move it to the working directory
   - Extract text using OCR
   - Classify the document
   - Move it to the output directory
   - Store metadata in the database

3. **Debug images are saved in subfolders:**
   - `~/pdf-processing/debug/` contains preprocessing debug images
   - Images are named with the original filename as prefix

### Accessing Processed Files

- **Processed documents:** `~/pdf-processing/output/`
- **Debug images:** `~/pdf-processing/debug/`
- **Database:** `~/pdf-processing/documents.db`

## Container Management

### Viewing Container Logs

```bash
# Web interface logs
docker logs pdf-magic-web

# Batch processing logs
docker logs pdf-magic-batch

# Follow logs in real-time
docker logs -f pdf-magic-batch
```

### Stopping Containers

```bash
# Stop web interface
docker stop pdf-magic-web

# Stop batch processing
docker stop pdf-magic-batch

# Stop and remove containers
docker stop pdf-magic-web pdf-magic-batch
docker rm pdf-magic-web pdf-magic-batch
```

### Updating the Application

1. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

2. **Rebuild the image:**
   ```bash
   docker build -t pdf-magic-monkey .
   ```

3. **Restart containers:**
   ```bash
   docker stop pdf-magic-web pdf-magic-batch
   docker rm pdf-magic-web pdf-magic-batch
   # Run the containers again with your preferred configuration
   ```

## Troubleshooting

### Common Issues

1. **Permission denied errors:**
   ```bash
   # Ensure the host directories have proper permissions
   sudo chmod -R 755 ~/pdf-processing/
   ```

2. **Port already in use:**
   ```bash
   # Use a different port for the web interface
   docker run -p 8080:5000 ... pdf-magic-monkey web
   ```

3. **Database locked errors:**
   - Ensure only one process is writing to the database
   - Stop all containers and restart if needed

4. **OCR not working:**
   - Check that input files are valid PDF or TIF files
   - Review container logs for Tesseract errors

### Debugging

**Enter a running container for debugging:**
```bash
docker exec -it pdf-magic-web bash
```

**Run a temporary container for testing:**
```bash
docker run --rm -it \
  -v ~/pdf-processing/input:/app/data/input \
  pdf-magic-monkey bash
```

## Advanced Usage

### Docker Compose (Optional)

Create a `docker-compose.yml` file for easier management:

```yaml
version: '3.8'
services:
  pdf-magic-web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ~/pdf-processing/input:/app/data/input
      - ~/pdf-processing/working:/app/data/working
      - ~/pdf-processing/output:/app/data/output
      - ~/pdf-processing/debug:/app/data/debug
      - ~/pdf-processing/documents.db:/app/data/documents.db
    command: web

  pdf-magic-batch:
    build: .
    volumes:
      - ~/pdf-processing/input:/app/data/input
      - ~/pdf-processing/working:/app/data/working
      - ~/pdf-processing/output:/app/data/output
      - ~/pdf-processing/debug:/app/data/debug
      - ~/pdf-processing/documents.db:/app/data/documents.db
    command: batch
```

Run with Docker Compose:
```bash
docker-compose up -d
```

## Security Considerations

- The containers run as root by default. For production use, consider running as a non-root user
- Ensure proper file permissions on mounted volumes
- Limit network access if running in production environments
- Regularly update the base image and dependencies

## Performance Tuning

- **Memory**: The application can be memory-intensive for large documents. Consider increasing Docker memory limits
- **CPU**: OCR processing is CPU-intensive. More CPU cores will improve processing speed
- **Storage**: Use SSD storage for better I/O performance, especially for the working directory

## Support

For issues specific to Docker deployment, check:
1. Container logs: `docker logs <container-name>`
2. Host system resources: `docker stats`
3. Volume mounts: Ensure all paths exist and have proper permissions
4. Network connectivity: Verify port mappings and firewall settings