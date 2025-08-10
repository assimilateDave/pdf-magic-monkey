# PDF Magic Monkey - Document Processing Workflow

## Overview

This system automatically processes PDF and TIF documents through OCR (Optical Character Recognition), classifies them, and stores the results in a database with a web-based review interface.

## New Processing Workflow (Updated)

The document processing workflow has been enhanced to use a dedicated final folder for fully processed files:

### Directory Structure

```
C:\PDF-Processing\
├── PDF_IN\          # Input folder - place new documents here (monitored)
├── PDF_working\     # Temporary processing folder (auto-created)
├── PDF_final\       # Final storage for processed documents (auto-created) ⭐ NEW
└── debug_imgs\      # Debug images from OCR preprocessing (auto-created)
```

### Processing Steps

1. **File Detection**: Documents placed in `PDF_IN` are automatically detected
2. **Initial Processing**: Files are moved to `PDF_working` for processing
3. **Text Extraction**: OCR is performed with preprocessing optimized for fax documents
4. **Document Classification**: Content is analyzed to determine document type (Invoice, Receipt, Report, etc.)
5. **Final Storage**: ⭐ **NEW** - Successfully processed files are moved to `PDF_final`
6. **Database Storage**: Document metadata and extracted text are stored with the final file path

### Key Improvements

- **Dedicated Final Storage**: Processed files are stored in `PDF_final` instead of remaining in the working directory
- **Complete File Paths**: Database now stores full file paths for better file management
- **Backward Compatibility**: Existing databases are automatically updated to support the new schema
- **Enhanced Web Interface**: UI displays document basenames while maintaining access to full file paths

## Database Schema

The database has been enhanced to support the new workflow:

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,              -- Full path to final file location
    basename TEXT,                        -- Just the filename for UI display
    document_type TEXT,                   -- Classified document type
    extracted_text TEXT,                  -- OCR extracted text
    flagged_for_reprocessing INTEGER DEFAULT 0,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## File Dependencies

- **processor.py**: Core processing logic with new FINAL_DIR workflow
- **main.py**: File watcher and processing coordinator
- **database.py**: Database operations with enhanced schema
- **app.py**: Flask web interface for document review
- **gui.py**: PyQt5 desktop interface (alternative)

## Configuration

### Directory Paths (in processor.py)

```python
WATCH_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_IN")      # Input folder
WORK_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_working")  # Processing folder  
FINAL_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_final")   # Final storage ⭐ NEW
```

### External Dependencies

- **Tesseract OCR**: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **Poppler**: `C:\PDF-Processing\poppler\Library\bin`

## Usage

### Starting the System

1. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Document Processing**:
   ```bash
   python main.py
   ```

3. **Start Web Interface** (optional):
   ```bash
   python app.py
   ```
   Then open http://localhost:5000

### Adding Documents

Simply copy PDF or TIF files to `C:\PDF-Processing\PDF_IN`. The system will:

1. Automatically detect new files
2. Process them through OCR and classification
3. Move them to the final storage folder
4. Update the database with the results

### Reviewing Results

- **Web Interface**: Use the Flask app to review extracted text and flag documents for reprocessing
- **Desktop GUI**: Use the PyQt5 interface for an alternative review experience
- **Database**: Query the SQLite database directly for advanced analysis

## Migration from Previous Version

The system automatically handles migration from the previous workflow:

- **Existing Files**: Files already in `PDF_working` can be manually moved to `PDF_final`
- **Database**: The schema is automatically updated to include the new `basename` column
- **Backward Compatibility**: The system will continue to work with existing databases

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure Tesseract and Poppler are installed in the expected paths
2. **Permission Errors**: Ensure the application has write access to all processing directories
3. **Database Errors**: The system will automatically create and update the database schema

### Directory Creation

All directories (`WORK_DIR`, `FINAL_DIR`, debug folders) are automatically created if they don't exist, ensuring the system works out of the box.

## API Endpoints (Flask App)

- `GET /api/documents` - List all processed documents
- `GET /api/document/<basename>/text` - Get extracted text for a document
- `POST /api/document/<basename>/flag` - Flag/unflag a document for reprocessing

The API now returns both the display filename (basename) and the full file path for complete file management.