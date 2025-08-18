import os
import sqlite3
from flask import Flask, render_template, jsonify, request, send_file, abort

DB_PATH = "documents.db"
FINAL_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_final")  # Final storage for processed documents

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)

def get_all_documents():
    conn = get_db_connection()
    docs = conn.execute(
        "SELECT id, file_name, basename, extracted_text, flagged_for_reprocessing, orientation_corrected FROM documents"
    ).fetchall()
    conn.close()
    return [
        {
            "id": doc["id"],
            "filename": doc["basename"] or os.path.basename(doc["file_name"]),  # Show basename for UI
            "file_path": doc["file_name"],  # Full path to final location
            "basename": doc["basename"],
            "extracted_text": doc["extracted_text"],
            "flagged": bool(doc["flagged_for_reprocessing"]),
            "orientation_corrected": bool(doc["orientation_corrected"] if doc["orientation_corrected"] is not None else False)
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

@app.route("/api/document/<basename>/pdf")
def api_document_pdf(basename):
    """Serve PDF file from the FINAL_DIR"""
    # First, find the document in the database to get the full file path
    conn = get_db_connection()
    doc = conn.execute(
        "SELECT file_name FROM documents WHERE basename = ?",
        (basename,)
    ).fetchone()
    conn.close()
    
    if not doc:
        abort(404, description="Document not found")
    
    file_path = doc["file_name"]
    
    # Check if the file exists
    if not os.path.exists(file_path):
        # Fallback: try to find the file in FINAL_DIR using basename
        fallback_path = os.path.join(FINAL_DIR, basename)
        if os.path.exists(fallback_path):
            file_path = fallback_path
        else:
            abort(404, description="PDF file not found")
    
    try:
        return send_file(file_path, mimetype='application/pdf')
    except Exception as e:
        abort(500, description=f"Error serving PDF: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)
    
