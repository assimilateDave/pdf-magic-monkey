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
    ├── original\    # Original images before preprocessing ⭐ NEW
    ├── orientation\ # Before/after orientation correction ⭐ NEW
    ├── basic\       # After basic preprocessing ⭐ NEW
    ├── denoise\     # After noise removal ⭐ NEW
    ├── morph\       # After morphological operations ⭐ NEW
    └── lines\       # After line removal ⭐ NEW
```

### Processing Steps

1. **File Detection**: Documents placed in `PDF_IN` are automatically detected
2. **Initial Processing**: Files are moved to `PDF_working` for processing
3. **Text Extraction**: OCR is performed with enhanced preprocessing pipeline:
   - **Page Orientation Correction** ⭐ **NEW**: Automatically detects and corrects page rotation (90°, 180°, 270°) using Tesseract OSD
   - **Basic Preprocessing**: Grayscale conversion, adaptive thresholding, median blur, sharpening, contrast enhancement
   - **Noise Removal** ⭐ **NEW**: OpenCV denoising (fastNlMeansDenoising or bilateralFilter)
   - **Morphological Operations** ⭐ **NEW**: Configurable dilation, erosion, opening, closing
   - **Line Removal** ⭐ **NEW**: Hough Line Transform to remove horizontal/vertical lines
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
    orientation_corrected INTEGER DEFAULT 0, -- Flag indicating if orientation was corrected
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

### OCR Preprocessing Configuration ⭐ NEW

The OCR preprocessing pipeline can be configured using the `ocr_preprocess.yaml` file in the project root. This allows you to enable/disable processing steps and tune their parameters for optimal results.

#### Configuration Structure

```yaml
# Page orientation correction (applied first)
orientation_correction:
  enabled: true

# Basic preprocessing (existing functionality)
basic_preprocessing:
  enabled: true
  adaptive_threshold:
    block_size: 15
    c_value: 11
  median_blur:
    kernel_size: 3
  sharpen:
    enabled: true
  contrast_enhancement:
    factor: 2.0

# Noise removal step
noise_removal:
  enabled: true  # Set to false to disable
  method: "fastNlMeansDenoising"  # or "bilateralFilter"
  h: 10  # Filter strength for fastNlMeansDenoising
  # ... additional parameters

# Morphological operations
morphological_operations:
  enabled: true
  operations:
    - type: "opening"  # "erosion", "dilation", "opening", "closing"
      kernel_size: [3, 3]
      kernel_shape: "ellipse"  # "rectangle", "ellipse", "cross"
      iterations: 1

# Line and border removal
line_removal:
  enabled: true
  threshold: 100  # Hough transform threshold
  min_line_length: 50
  horizontal_lines: true
  vertical_lines: true
  angle_tolerance: 10  # degrees

# Debug settings
debug:
  save_images: true
  base_folder: "debug_imgs"
  subfolders:
    original: "original"
    orientation: "orientation"
    basic: "basic"
    denoise: "denoise"
    morph: "morph"
    lines: "lines"
```

#### Tuning Guidelines

- **Page Orientation Correction**: Set `enabled: false` to disable if your documents are always correctly oriented, or if Tesseract OSD causes issues with your specific document types
- **Noise Removal**: Increase `h` parameter for more aggressive denoising, decrease for preserving fine details
- **Morphological Operations**: Use "opening" to remove noise, "closing" to fill gaps. Adjust kernel size based on document characteristics
- **Line Removal**: Adjust `threshold` and `min_line_length` based on the types of lines you want to remove
- **Debug Images**: Set `save_images: false` to disable debug image generation for faster processing

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
   
   **Note**: The enhanced OCR preprocessing requires PyYAML for configuration management. This is now included in requirements.txt.

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

## Orientation Correction Tracking ⭐ NEW

The system now automatically tracks when document orientation correction is applied during processing:

### Features

- **Database Storage**: The `orientation_corrected` field in the database indicates if a document's orientation was corrected (1) or not (0)
- **Automatic Detection**: During OCR preprocessing, Tesseract's OSD (Orientation and Script Detection) detects incorrect orientation
- **Visual Indicators**: The web interface displays a blue "📐 ROTATED" badge next to documents that had their orientation corrected
- **API Integration**: The `/api/documents` endpoint includes the `orientation_corrected` field in responses

### How It Works

1. **Processing**: When a document is processed, each page is analyzed for correct orientation
2. **Correction**: If rotation is needed, the image is rotated and the correction is tracked
3. **Storage**: The orientation correction status is stored in the database along with other document metadata  
4. **Display**: Users can see which documents required orientation correction in the web interface

This ensures users know if the PDF they see has been automatically rotated for correct orientation, providing transparency about the processing steps applied.

## Clinical Document Classification with medSpaCy ⭐ NEW

The system now includes advanced clinical document classification and entity extraction powered by medSpaCy, specifically designed for medical documents:

### Features

- **Clinical Document Types**: Automatically classifies documents as:
  - `referral`: Referral letters and consultation requests
  - `order`: Medical orders, prescriptions, lab orders
  - `progress_note`: Progress notes, SOAP notes, clinical assessments
  - `correspondence`: Letters and communications between providers
  - `other`: Other document types
- **Entity Extraction**: Extracts clinical entities including medications, conditions, procedures, and anatomy
- **Machine Learning**: Uses scikit-learn with customizable training data
- **Fallback Support**: Falls back to keyword-based classification if medSpaCy is unavailable

### Quick Start

1. **Install Dependencies** (included in requirements.txt):
   ```bash
   pip install medspacy scikit-learn
   python -m spacy download en_core_web_sm
   ```

2. **Train the Classifier**:
   ```bash
   python example_medspacy_integration.py
   ```

3. **Update Database Schema**:
   ```sql
   ALTER TABLE documents ADD COLUMN extracted_entities TEXT;
   ```

### Database Schema

The enhanced database now includes:

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,              -- Full path to final file location
    basename TEXT,                        -- Just the filename for UI display
    document_type TEXT,                   -- Clinical document type (referral, order, etc.)
    extracted_text TEXT,                  -- OCR extracted text
    extracted_entities TEXT,              -- ⭐ NEW: JSON with clinical entities
    flagged_for_reprocessing INTEGER DEFAULT 0,
    orientation_corrected INTEGER DEFAULT 0,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Usage Examples

**Query by Document Type**:
```sql
SELECT * FROM documents WHERE document_type = 'referral';
SELECT * FROM documents WHERE document_type = 'order';
```

**Search Clinical Entities**:
```sql
SELECT * FROM documents WHERE extracted_entities LIKE '%hypertension%';
SELECT * FROM documents WHERE extracted_entities LIKE '%medication%';
```

**Document Type Distribution**:
```sql
SELECT document_type, COUNT(*) as count 
FROM documents 
GROUP BY document_type 
ORDER BY count DESC;
```

### Customization

To customize the classifier for your specific clinical documents:

1. **Edit Training Data**: Modify the `train_data` list in `example_medspacy_integration.py`
2. **Add Examples**: Include diverse examples of each document type
3. **Retrain**: Run the training script to update the model
4. **Test**: The system will automatically use your custom-trained model

### Integration Details

- **Processing Workflow**: OCR Text Extraction → medSpaCy Classification & Entity Extraction → Database Storage
- **Automatic Integration**: Classification occurs automatically after OCR in the existing pipeline
- **Backward Compatibility**: Existing functionality is preserved; new features enhance the system
- **Performance**: Entity extraction adds minimal processing time to the pipeline