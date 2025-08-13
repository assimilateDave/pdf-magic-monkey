#!/bin/bash
set -e

# Initialize database if it doesn't exist
python3 -c "from database import init_db; init_db()"

# Create directories if they don't exist
mkdir -p "${WATCH_DIR}" "${WORK_DIR}" "${FINAL_DIR}" "${DEBUG_DIR}"

# Handle different run modes
case "$1" in
    web)
        echo "Starting web interface on port 5000..."
        exec python3 app.py
        ;;
    batch)
        echo "Starting batch processing (watching ${WATCH_DIR})..."
        exec python3 main.py
        ;;
    *)
        echo "Usage: docker run [options] image [web|batch]"
        echo "  web   - Start web interface (default)"
        echo "  batch - Start batch file processing"
        exit 1
        ;;
esac