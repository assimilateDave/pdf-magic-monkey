## Document OCR Review Web GUI

### Overview

This adds a web-based GUI for reviewing OCR-processed documents.  
You can view the list of processed documents, see their extracted text, and inspect debug images, all in your browser.

---

### Quick Start Instructions

#### 1. **Install requirements**
Open your command prompt and run:
```bash
pip install flask
```

#### 2. **File placement**
- Place `app.py` in your project root (same folder as your processing scripts).
- Place the `index.html` file in a subfolder named `templates` (create if missing):
  ```
  your-project/
    app.py
    templates/
      index.html
  ```

#### 3. **Check your folders**
- Make sure your processed documents are in `C:\PDF-Processing\PDF_working`
- Make sure your debug images are in `C:\PDF-Processing\debug_imgs`
- (Optional) If you save extracted text as `.txt` files in `PDF_working`, the GUI will display them automatically.

#### 4. **Run the web server**
In your project folder, open a command prompt and run:
```bash
python app.py
```
You should see output ending with something like:
```
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

#### 5. **Open the GUI**
Open your web browser and go to:
```
http://localhost:5000
```

#### 6. **Using the GUI**
- Click a document in the list to see its OCR text and debug images.
- Use this to validate the extraction and decide if reprocessing is needed.

---

### Troubleshooting

- If you see `[No extracted text file found.]`, check if `.txt` files are being saved in `PDF_working` with the same name as the document.
- If you see no debug images, check that images are actually being saved in the debug folder and named with the document basename.
- To stop the server, return to your command prompt and press `Ctrl+C`.

---

### Customization

- You can adjust folder paths in `app.py` if your setup is different.
- For advanced features (such as marking documents for reprocessing), ask for further enhancements!
