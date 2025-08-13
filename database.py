import sqlite3
import os

DB_NAME = os.environ.get('DB_PATH', "documents.db")

def init_db():
    # Ensure the directory for the database exists
    db_dir = os.path.dirname(DB_NAME)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    create_table = not os.path.exists(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    if create_table:
        with conn:
            conn.execute(
                """
                CREATE TABLE documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    basename TEXT,
                    document_type TEXT,
                    extracted_text TEXT,
                    flagged_for_reprocessing INTEGER DEFAULT 0,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
    else:
        # Add basename column if it doesn't exist (for backward compatibility)
        try:
            conn.execute("ALTER TABLE documents ADD COLUMN basename TEXT")
        except sqlite3.OperationalError:
            # Column already exists or other error, ignore
            pass
    return conn

def insert_document(final_file_path, document_type, extracted_text):
    """
    Insert a document record with the final file path.
    file_name stores the full path, basename stores just the filename for compatibility.
    """
    conn = sqlite3.connect(DB_NAME)
    basename = os.path.basename(final_file_path)
    with conn:
        conn.execute(
            "INSERT INTO documents (file_name, basename, document_type, extracted_text) VALUES (?, ?, ?, ?)",
            (final_file_path, basename, document_type, extracted_text)
        )