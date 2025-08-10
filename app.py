import os
import sqlite3
from flask import Flask, render_template, jsonify, request

DB_PATH = "documents.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)

def get_all_documents():
    conn = get_db_connection()
    docs = conn.execute(
        "SELECT id, file_name, basename, extracted_text, flagged_for_reprocessing FROM documents"
    ).fetchall()
    conn.close()
    return [
        {
            "id": doc["id"],
            "filename": doc["basename"] or os.path.basename(doc["file_name"]),  # Show basename for UI
            "file_path": doc["file_name"],  # Full path to final location
            "basename": doc["basename"],
            "extracted_text": doc["extracted_text"],
            "flagged": bool(doc["flagged_for_reprocessing"])
        }
        for doc in docs
    ]

def get_document_text_and_flag(basename):
    conn = get_db_connection()
    doc = conn.execute(
        "SELECT extracted_text, flagged_for_reprocessing FROM documents WHERE basename = ?",
        (basename,)
    ).fetchone()
    conn.close()
    if doc:
        return doc["extracted_text"], bool(doc["flagged_for_reprocessing"])
    else:
        return None, None

def set_flag_for_reprocessing(basename, flag_value):
    conn = get_db_connection()
    conn.execute(
        "UPDATE documents SET flagged_for_reprocessing = ? WHERE basename = ?",
        (1 if flag_value else 0, basename)
    )
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/documents")
def api_documents():
    return jsonify(get_all_documents())

@app.route("/api/document/<basename>/text")
def api_document_text(basename):
    text, flagged = get_document_text_and_flag(basename)
    if text is None:
        return jsonify({"text": "[No extracted text found.]", "flagged": False})
    return jsonify({"text": text, "flagged": flagged})

@app.route("/api/document/<basename>/flag", methods=["POST"])
def api_flag_document(basename):
    data = request.get_json()
    flag_value = data.get("flag", False)
    set_flag_for_reprocessing(basename, flag_value)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)
    
