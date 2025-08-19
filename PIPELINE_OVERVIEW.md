# PDF Magic Monkey: Current Pipeline Overview & Next Steps

_Last updated: 2025-08-19_

---

## 🏗️ Current Processing Pipeline Outline

1. **File Detection and Intake**
   - New PDFs are detected in the `PDF_IN` directory.
   - Files are moved to `PDF_working` for processing.

2. **Page/Image Pre-processing Pipeline** (in `processor.py`, called per page)
   - **a. (Planned) Page Orientation Correction**  
     *New*: Detect and correct page rotation using Tesseract OSD.
   - **b. Basic Preprocessing**
     - Convert to grayscale
     - Adaptive thresholding (binarization)
     - Median blur (noise smoothing)
     - Sharpening (optional)
     - Contrast enhancement (optional)
   - **c. Noise Removal**
     - OpenCV denoising (e.g., fastNlMeansDenoising, bilateralFilter)
   - **d. Morphological Operations**
     - Configurable: opening, closing, dilation, erosion (for cleanup)
   - **e. Line and Border Removal**
     - Hough Transform-based removal of horizontal/vertical lines

3. **OCR Text Extraction**
   - Run OCR (Tesseract) on pre-processed images to extract text.

4. **Document Classification**  
   - Analyze extracted text and/or metadata to determine type (invoice, report, etc.)
   - *Currently basic; planned for LLM/NLP upgrade.*

5. **Final Storage**
   - Move processed files to `PDF_final`.
   - Store extracted text and metadata in a database.

---

## 📈 Potential Next Steps & Enhancements

1. **Implement Page Orientation Correction**
   - Insert as the first step in pre-processing.
   - Configurable in YAML; debug image output.

2. **Upgrade Document Classification**
   - Move to post-OCR, using full extracted text.
   - Incorporate NLP or LLM-based semantic analysis for robust classification.

3. **Integrate Advanced NLP/LLM Analysis**
   - Extract entities, key values, and semantic meaning from OCR output.
   - Use for classification, indexing, or downstream workflow triggers.

4. **Refactor/Modularize Pipeline**
   - Ensure each pre-processing step is cleanly modular, testable, and documented.
   - Make it easy to add/remove steps via config.

5. **Improve Debugging & Logging**
   - Extend debug image saving for each step.
   - Better pipeline logging for monitoring and troubleshooting.

6. **Performance Optimizations**
   - Batch processing, parallelism, or GPU acceleration.
   - Caching intermediate results for large files.

7. **Error Handling & Recovery**
   - Robust handling of failed pages/pdfs (skip, retry, log).
   - Graceful fallback if one step fails.

8. **Enhanced Configuration**
   - More granular per-document or per-batch config overrides.
   - Auto-tuning based on document characteristics.

---

## ✨ Summary Table

| Stage             | What It Does                        | Status           | Next Enhancements            |
|-------------------|-------------------------------------|------------------|------------------------------|
| Intake            | Detect/move PDFs for processing     | Working          | N/A                          |
| Page Preprocessing| Grayscale, threshold, denoise, etc. | Working (+WIP)   | Add orientation correction   |
| OCR Extraction    | Get text from images                | Working          | N/A                          |
| Classification    | Categorize document type            | Basic            | NLP/LLM-based, move post-OCR |
| Final Storage     | Store files/output                  | Working          | N/A                          |

---

_Contact: assimilateDave for pipeline questions or suggestions._