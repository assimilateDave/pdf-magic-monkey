import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from processor import process_document, WATCH_DIR
from database import insert_document

def wait_for_file_release(filepath, timeout=60):
    """
    Wait until file is unlocked and its size is stable.
    :param filepath: Path to the file to wait for.
    :param timeout: Maximum seconds to wait before raising TimeoutError.
    """
    start = time.time()
    last_size = -1
    while True:
        try:
            current_size = os.path.getsize(filepath)
            with open(filepath, 'rb'):
                pass
            if current_size == last_size:
                # File size hasn't changed, so it's probably done writing.
                return
            last_size = current_size
        except Exception:
            # File might still be locked or incomplete.
            pass
        if time.time() - start > timeout:
            raise TimeoutError(f"File {filepath} not released after {timeout} seconds.")
        time.sleep(1)
        
class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Only process files (not directories)
        if event.is_directory:
            return
        file_path = event.src_path
        # Only process PDF and TIF files
        if file_path.lower().endswith(('.pdf', '.tif', '.tiff')):
            print(f"New file detected: {file_path}")
            wait_for_file_release(file_path, timeout=60)  # Adjust timeout as needed
            final_file_path, doc_type, extracted_text = process_document(file_path)
            insert_document(final_file_path, doc_type, extracted_text)
            print(f"Processed {os.path.basename(final_file_path)} as {doc_type}, stored in {final_file_path}")

if __name__ == "__main__":
    if not os.path.isdir(WATCH_DIR):
        os.makedirs(WATCH_DIR)
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    print(f"Watching folder: {WATCH_DIR}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
