import sqlite3
import os

DB_NAME = "documents.db"

def init_db():
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
                    orientation_corrected INTEGER DEFAULT 0,
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
        
        # Add orientation_corrected column if it doesn't exist
        try:
            conn.execute("ALTER TABLE documents ADD COLUMN orientation_corrected INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            # Column already exists or other error, ignore
            pass
    return conn

def insert_document(final_file_path, document_type, extracted_text, orientation_corrected=0):
    """
    Insert a document record with the final file path.
    file_name stores the full path, basename stores just the filename for compatibility.
    """
    conn = sqlite3.connect(DB_NAME)
    basename = os.path.basename(final_file_path)
    with conn:
        conn.execute(
            "INSERT INTO documents (file_name, basename, document_type, extracted_text, orientation_corrected) VALUES (?, ?, ?, ?, ?)",
            (final_file_path, basename, document_type, extracted_text, orientation_corrected)
        )