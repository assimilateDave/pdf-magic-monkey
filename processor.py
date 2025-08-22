import os
import cv2
import numpy as np
import shutil
import yaml
import math
import tempfile
import time
import datetime
import json
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract

# Import clinical document classifier for medSpaCy integration
try:
    from clinical_document_classifier import ClinicalDocumentClassifier
    MEDSPACY_AVAILABLE = True
except ImportError:
    print("Warning: medSpaCy classifier not available. Using fallback classification.")
    MEDSPACY_AVAILABLE = False

# Set tesseract path based on the operating system
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:  # Unix/Linux systems
    # Use the system tesseract (should be in PATH after installation)
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

# Define your working directories here  
if os.name == 'nt':  # Windows
    WATCH_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_IN")    # Input folder for new documents
    WORK_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_working")  # Temporary processing folder
    FINAL_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_final")   # Final storage for processed documents
else:  # Unix/Linux systems
    base_dir = os.path.abspath("PDF-Processing")
    WATCH_DIR = os.path.join(base_dir, "PDF_IN")    # Input folder for new documents
    WORK_DIR = os.path.join(base_dir, "PDF_working")  # Temporary processing folder
    FINAL_DIR = os.path.join(base_dir, "PDF_final")   # Final storage for processed documents

def log_timing(step_name, duration, base_name, page_idx):
    """
    Log timing information for preprocessing steps.
    
    Args:
        step_name: Name of the preprocessing step
        duration: Duration in seconds  
        base_name: Base filename being processed
        page_idx: Page index
    """
    # Check if timing logging is enabled
    if not CONFIG.get('debug', {}).get('log_timings', False):
        return
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.abspath("Pre_Proc_logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create timestamped log filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(logs_dir, f"preprocessing_timings_{timestamp}.log")
    
    # Format timing entry
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{current_time}] {base_name}_page_{page_idx} | {step_name} | {duration:.3f}s\n"
    
    # Append to log file
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        # Silently fail to avoid breaking processing if logging fails
        pass

def time_preprocessing_step(func):
    """
    Decorator to time preprocessing steps and log if enabled.
    
    Args:
        func: Preprocessing function to wrap
        
    Returns:
        Wrapped function that logs timing
    """
    def wrapper(*args, **kwargs):
        # Extract step name from function name
        step_name = func.__name__.replace('preprocess_', '')
        
        # Get base_name and page_idx from args if available
        base_name = args[1] if len(args) > 1 else kwargs.get('base_name', 'unknown')
        page_idx = args[2] if len(args) > 2 else kwargs.get('page_idx', 0)
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        duration = end_time - start_time
        log_timing(step_name, duration, base_name, page_idx)
        
        return result
    return wrapper

# Load OCR preprocessing configuration
def load_config():
    """Load OCR preprocessing configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), 'ocr_preprocess.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}, using default settings")
        return get_default_config()
    except Exception as e:
        print(f"Error loading config: {e}, using default settings")
        return get_default_config()

def get_default_config():
    """Return default configuration if config file is not available."""
    return {
        'orientation_correction': {'enabled': True},
        'basic_preprocessing': {'enabled': True},
        'noise_removal': {'enabled': False},
        'morphological_operations': {'enabled': False},
        'line_removal': {'enabled': False},
        'debug': {
            'save_images': True,
            'base_folder': 'debug_imgs',
            'log_timings': False,
            'subfolders': {
                'original': 'original',
                'orientation': 'orientation',
                'basic': 'basic',
                'denoise': 'denoise',
                'morph': 'morph',
                'lines': 'lines'
            }
        }
    }

# Global config instance
CONFIG = load_config()

def move_to_work_folder(file_path):
    """Move file from the watch folder to the work folder."""
    if not os.path.isdir(WORK_DIR):
        os.makedirs(WORK_DIR)
    dest_path = os.path.join(WORK_DIR, os.path.basename(file_path))
    shutil.move(file_path, dest_path)
    return dest_path

def move_to_final_folder(file_path):
    """
    Move file from the work folder to the final folder after successful processing.
    Creates the final directory if it doesn't exist (backward compatibility).
    """
    if not os.path.isdir(FINAL_DIR):
        os.makedirs(FINAL_DIR)
    dest_path = os.path.join(FINAL_DIR, os.path.basename(file_path))
    shutil.move(file_path, dest_path)
    return dest_path

def save_debug_image(img, base_name, page_idx, step_name, subfolder=None):
    """
    Save debug image with organized folder structure.
    
    Args:
        img: PIL Image or numpy array
        base_name: Base filename without extension
        page_idx: Page index
        step_name: Name of the processing step
        subfolder: Subfolder name from config (optional)
    """
    if not CONFIG.get('debug', {}).get('save_images', True):
        return
    
    debug_base = CONFIG.get('debug', {}).get('base_folder', 'debug_imgs')
    if not os.path.isabs(debug_base):
        debug_base = os.path.abspath(debug_base)
    
    if subfolder:
        debug_folder = os.path.join(debug_base, subfolder)
    else:
        debug_folder = debug_base
    
    os.makedirs(debug_folder, exist_ok=True)
    
    debug_path = os.path.join(debug_folder, f'{base_name}_{step_name}_page_{page_idx}.png')
    
    # Convert numpy array to PIL if needed
    if isinstance(img, np.ndarray):
        if len(img.shape) == 2:  # Grayscale
            img = Image.fromarray(img)
        else:  # Color
            img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    img.save(debug_path)
    return debug_path

@time_preprocessing_step
def preprocess_orientation_correction(img, base_name, page_idx):
    """
    Apply page orientation correction using Tesseract's OSD (Orientation and Script Detection).
    
    Args:
        img: PIL Image
        base_name: Base filename for debug images
        page_idx: Page index
        
    Returns:
        tuple: (PIL Image after orientation correction, bool indicating if correction was applied)
    """
    config = CONFIG.get('orientation_correction', {})
    if not config.get('enabled', True):
        return img, False
    
    try:
        # Save original image before orientation correction
        save_debug_image(img, base_name, page_idx, 'before_orientation',
                        CONFIG.get('debug', {}).get('subfolders', {}).get('orientation'))
        
        # Use Tesseract OSD to detect orientation
        osd = pytesseract.image_to_osd(img)
        
        # Parse the OSD output to extract rotation angle
        rotation_angle = 0
        for line in osd.split('\n'):
            if 'Rotate:' in line:
                rotation_angle = int(line.split(':')[1].strip())
                break
        
        # Apply rotation correction if needed
        corrected_img = img
        orientation_was_corrected = False
        if rotation_angle != 0:
            print(f"Detected {rotation_angle}° rotation, correcting orientation...")
            # Rotate counter-clockwise to correct the orientation
            corrected_img = img.rotate(-rotation_angle, expand=True, fillcolor='white')
            orientation_was_corrected = True
        
        # Save corrected image
        save_debug_image(corrected_img, base_name, page_idx, 'after_orientation',
                        CONFIG.get('debug', {}).get('subfolders', {}).get('orientation'))
        
        return corrected_img, orientation_was_corrected
        
    except Exception as e:
        print(f"Warning: Orientation correction failed for page {page_idx}: {e}")
        # Return original image if orientation detection fails
        return img, False

@time_preprocessing_step
def preprocess_basic(img, base_name, page_idx):
    """
    Apply basic preprocessing steps (existing functionality).
    
    Args:
        img: PIL Image
        base_name: Base filename for debug images
        page_idx: Page index
        
    Returns:
        PIL Image after basic preprocessing
    """
    config = CONFIG.get('basic_preprocessing', {})
    if not config.get('enabled', True):
        return img
    
    # Convert to grayscale
    img_array = np.array(img.convert('L'))
    
    # Save original for debugging
    save_debug_image(img, base_name, page_idx, 'original', 
                    CONFIG.get('debug', {}).get('subfolders', {}).get('original'))
    
    # Adaptive thresholding to binarize
    threshold_config = config.get('adaptive_threshold', {})
    img_array = cv2.adaptiveThreshold(
        img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 
        threshold_config.get('block_size', 15), 
        threshold_config.get('c_value', 11)
    )
    
    # Median blur to reduce noise
    blur_config = config.get('median_blur', {})
    img_array = cv2.medianBlur(img_array, blur_config.get('kernel_size', 3))
    
    # Convert back to PIL for further processing
    pil_img = Image.fromarray(img_array)
    
    # Sharpen the image
    if config.get('sharpen', {}).get('enabled', True):
        pil_img = pil_img.filter(ImageFilter.SHARPEN)
    
    # Enhance contrast
    contrast_config = config.get('contrast_enhancement', {})
    if contrast_config.get('factor', 2.0) != 1.0:
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(contrast_config.get('factor', 2.0))
    
    # Save basic preprocessing result
    save_debug_image(pil_img, base_name, page_idx, 'basic',
                    CONFIG.get('debug', {}).get('subfolders', {}).get('basic'))
    
    return pil_img

@time_preprocessing_step
def preprocess_noise_removal(img, base_name, page_idx):
    """
    Apply noise removal preprocessing.
    
    Args:
        img: PIL Image
        base_name: Base filename for debug images
        page_idx: Page index
        
    Returns:
        PIL Image after noise removal
    """
    config = CONFIG.get('noise_removal', {})
    if not config.get('enabled', False):
        return img
    
    # Convert PIL to numpy array
    img_array = np.array(img)
    
    method = config.get('method', 'fastNlMeansDenoising')
    
    if method == 'fastNlMeansDenoising':
        img_array = cv2.fastNlMeansDenoising(
            img_array,
            None,
            h=config.get('h', 10),
            templateWindowSize=config.get('templateWindowSize', 7),
            searchWindowSize=config.get('searchWindowSize', 21)
        )
    elif method == 'bilateralFilter':
        img_array = cv2.bilateralFilter(
            img_array,
            d=config.get('d', 9),
            sigmaColor=config.get('sigmaColor', 75),
            sigmaSpace=config.get('sigmaSpace', 75)
        )
    
    # Convert back to PIL
    result_img = Image.fromarray(img_array)
    
    # Save debug image
    save_debug_image(result_img, base_name, page_idx, 'denoise',
                    CONFIG.get('debug', {}).get('subfolders', {}).get('denoise'))
    
    return result_img

@time_preprocessing_step
def preprocess_morphological_operations(img, base_name, page_idx):
    """
    Apply morphological operations.
    
    Args:
        img: PIL Image
        base_name: Base filename for debug images
        page_idx: Page index
        
    Returns:
        PIL Image after morphological operations
    """
    config = CONFIG.get('morphological_operations', {})
    if not config.get('enabled', False):
        return img
    
    # Convert PIL to numpy array
    img_array = np.array(img)
    
    operations = config.get('operations', [])
    
    for op_config in operations:
        op_type = op_config.get('type', 'opening')
        kernel_size = op_config.get('kernel_size', [3, 3])
        kernel_shape = op_config.get('kernel_shape', 'ellipse')
        iterations = op_config.get('iterations', 1)
        
        # Create kernel
        if kernel_shape == 'ellipse':
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, tuple(kernel_size))
        elif kernel_shape == 'cross':
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, tuple(kernel_size))
        else:  # rectangle
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, tuple(kernel_size))
        
        # Apply operation
        if op_type == 'erosion':
            img_array = cv2.erode(img_array, kernel, iterations=iterations)
        elif op_type == 'dilation':
            img_array = cv2.dilate(img_array, kernel, iterations=iterations)
        elif op_type == 'opening':
            img_array = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, kernel, iterations=iterations)
        elif op_type == 'closing':
            img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel, iterations=iterations)
    
    # Convert back to PIL
    result_img = Image.fromarray(img_array)
    
    # Save debug image
    save_debug_image(result_img, base_name, page_idx, 'morph',
                    CONFIG.get('debug', {}).get('subfolders', {}).get('morph'))
    
    return result_img

@time_preprocessing_step
def preprocess_line_removal(img, base_name, page_idx):
    """
    Apply line and border removal using Hough Line Transform.
    
    Args:
        img: PIL Image
        base_name: Base filename for debug images
        page_idx: Page index
        
    Returns:
        PIL Image after line removal
    """
    config = CONFIG.get('line_removal', {})
    if not config.get('enabled', False):
        return img
    
    # Convert PIL to numpy array
    img_array = np.array(img)
    
    # Hough Line Transform parameters
    rho = config.get('rho', 1)
    theta_degrees = config.get('theta_degrees', 1)
    theta = math.radians(theta_degrees)
    threshold = config.get('threshold', 100)
    min_line_length = config.get('min_line_length', 50)
    max_line_gap = config.get('max_line_gap', 10)
    
    # Line removal parameters
    line_thickness = config.get('line_thickness', 3)
    remove_horizontal = config.get('horizontal_lines', True)
    remove_vertical = config.get('vertical_lines', True)
    angle_tolerance = config.get('angle_tolerance', 10)
    
    # Detect lines using HoughLinesP
    lines = cv2.HoughLinesP(
        img_array, rho, theta, threshold,
        minLineLength=min_line_length, maxLineGap=max_line_gap
    )
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Calculate angle of the line
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            angle = abs(angle)
            
            # Check if line is horizontal or vertical within tolerance
            is_horizontal = angle <= angle_tolerance or angle >= (180 - angle_tolerance)
            is_vertical = abs(angle - 90) <= angle_tolerance
            
            # Remove the line if it matches our criteria
            if (remove_horizontal and is_horizontal) or (remove_vertical and is_vertical):
                cv2.line(img_array, (x1, y1), (x2, y2), 255, line_thickness)
    
    # Convert back to PIL
    result_img = Image.fromarray(img_array)
    
    # Save debug image
    save_debug_image(result_img, base_name, page_idx, 'lines',
                    CONFIG.get('debug', {}).get('subfolders', {}).get('lines'))
    
    return result_img

def generate_corrected_pdf(original_pdf_path, processed_pages):
    """
    Generate a new PDF file from processed PIL Images.
    
    Args:
        original_pdf_path: Path to the original PDF file
        processed_pages: List of PIL Images (one per page)
        
    Returns:
        str: Path to the generated corrected PDF, or None if failed
    """
    if not processed_pages:
        return None
    
    try:
        # Create temporary file for the corrected PDF
        base_name = os.path.splitext(os.path.basename(original_pdf_path))[0]
        temp_dir = os.path.dirname(original_pdf_path)
        temp_pdf_path = os.path.join(temp_dir, f"{base_name}_corrected.pdf")
        
        # Convert all images to RGB mode (required for PDF)
        rgb_pages = []
        for page in processed_pages:
            if page.mode != 'RGB':
                rgb_pages.append(page.convert('RGB'))
            else:
                rgb_pages.append(page)
        
        # Save as multi-page PDF
        if rgb_pages:
            rgb_pages[0].save(
                temp_pdf_path, 
                "PDF", 
                save_all=True, 
                append_images=rgb_pages[1:] if len(rgb_pages) > 1 else []
            )
            print(f"Successfully generated corrected PDF: {temp_pdf_path}")
            return temp_pdf_path
        
    except Exception as e:
        print(f"Error generating corrected PDF: {e}")
        return None

def classify_document(file_path, extracted_text):
    """
    Identify and classify the document type based on the file content.
    Uses medSpaCy clinical document classifier when available, falls back to keyword matching.
    
    Returns:
        tuple: (document_type, extracted_entities_json)
        - document_type: Classification result (referral, order, progress_note, correspondence, other)
        - extracted_entities_json: JSON string of clinical entities (None if medSpaCy not available)
    """
    extracted_entities_json = None
    
    # Try to use medSpaCy clinical classifier
    if MEDSPACY_AVAILABLE:
        try:
            # Initialize classifier (will load existing model if available)
            classifier = ClinicalDocumentClassifier()
            
            # Get prediction and entity extraction
            result = classifier.predict(extracted_text)
            
            document_type = result['document_type']
            extracted_entities_json = json.dumps(result['extracted_entities'])
            
            print(f"Clinical classification: {document_type} (confidence: {result['confidence']:.2f})")
            print(f"Entities found: {len(result['extracted_entities']['clinical_entities'])}")
            
            return document_type, extracted_entities_json
            
        except Exception as e:
            print(f"Error using clinical classifier, falling back to keyword matching: {e}")
    
    # Fallback to original keyword-based classification
    text_lower = extracted_text.lower()
    
    # Clinical document keywords (updated for medical context)
    if any(word in text_lower for word in ["referral", "refer", "consultation", "please see"]):
        document_type = "referral"
    elif any(word in text_lower for word in ["order", "prescription", "rx", "lab order", "prescribe"]):
        document_type = "order"  
    elif any(word in text_lower for word in ["progress note", "soap", "assessment", "plan", "clinical note"]):
        document_type = "progress_note"
    elif any(word in text_lower for word in ["letter", "dear", "sincerely", "correspondence"]):
        document_type = "correspondence"
    elif any(word in text_lower for word in ["invoice", "receipt", "report"]):
        # Keep original classifications for non-clinical documents
        if "invoice" in text_lower:
            document_type = "Invoice"
        elif "receipt" in text_lower:
            document_type = "Receipt" 
        elif "report" in text_lower:
            document_type = "Report"
        else:
            document_type = "other"
    else:
        document_type = "other"
    
    print(f"Keyword-based classification: {document_type}")
    return document_type, extracted_entities_json

def preprocess_fax_page(pil_img, base_name="image", page_idx=0):
    """
    Preprocess a PIL image of a fax PDF page for improved OCR accuracy.
    Now uses modular preprocessing steps that can be configured.
    
    Args:
        pil_img: PIL Image to preprocess
        base_name: Base filename for debug images
        page_idx: Page index for debug images
        
    Returns:
        tuple: (PIL Image after all enabled preprocessing steps, bool indicating if orientation was corrected)
    """
    # Apply preprocessing steps in order
    img, orientation_corrected = preprocess_orientation_correction(pil_img, base_name, page_idx)
    img = preprocess_basic(img, base_name, page_idx)
    img = preprocess_noise_removal(img, base_name, page_idx)
    img = preprocess_morphological_operations(img, base_name, page_idx)
    img = preprocess_line_removal(img, base_name, page_idx)
    
    return img, orientation_corrected

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF, using preprocessing optimized for faxed documents.
    Saves debug images with original filename as prefix.
    Skips extraction of the top 60px of each page.
    
    NEW: If any page requires orientation correction, generates a new PDF file
    with all pages (corrected and uncorrected) in their proper orientation.
    
    Returns:
        tuple: (extracted_text, bool indicating if any page had orientation corrected)
    """
    debug_folder = os.path.abspath("debug_imgs")
    os.makedirs(debug_folder, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    try:
        # Use higher DPI for faxes
        # Try system poppler first, then Windows path if available
        try:
            pages = convert_from_path(file_path, dpi=400)
        except Exception:
            # Fallback for Windows systems
            pages = convert_from_path(
                file_path, 
                dpi=400, 
                poppler_path=r"C:\PDF-Processing\poppler\Library\bin"
            )
        text = ""
        any_page_orientation_corrected = False
        processed_pages = []  # NEW: Collect processed images for PDF regeneration
        
        for i, page in enumerate(pages):
            # Preprocessing step here with base_name and page index:
            proc_page, page_orientation_corrected = preprocess_fax_page(page, base_name, i)
            
            # Track if any page had orientation correction
            if page_orientation_corrected:
                any_page_orientation_corrected = True
            
            # NEW: Collect the processed page image
            processed_pages.append(proc_page)
            
            # Save final processed image for backward compatibility
            debug_path = os.path.join(
                debug_folder, f'{base_name}_debug_page_{i}.png'
            )
            proc_page.save(debug_path)
            
            # Crop top 60px
            width, height = proc_page.size
            cropped_page = proc_page.crop((0, 60, width, height))
            config = '--oem 1 --psm 3'
            text += pytesseract.image_to_string(cropped_page, config=config, lang='eng')
        
        # NEW: If orientation correction occurred, generate corrected PDF
        if any_page_orientation_corrected and processed_pages:
            corrected_pdf_path = generate_corrected_pdf(file_path, processed_pages)
            if corrected_pdf_path:
                # Replace the original file with the corrected one
                shutil.move(corrected_pdf_path, file_path)
                print(f"Generated corrected PDF with orientation fixes: {os.path.basename(file_path)}")
        
        return text, any_page_orientation_corrected
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return "", False

def extract_text_from_tif(file_path):
    """
    Use OCR to extract text from a TIF, skipping the top 60px.
    
    NEW: If orientation correction occurs, generates a new TIF file
    with the corrected orientation.
    
    Returns:
        tuple: (extracted_text, bool indicating if orientation was corrected)
    """
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    try:
        img = Image.open(file_path)
        proc_img, orientation_corrected = preprocess_fax_page(img, base_name, 0)
        
        # NEW: If orientation correction occurred, save corrected TIF
        if orientation_corrected:
            # Convert to RGB if not already (for consistent saving)
            if proc_img.mode != 'RGB':
                proc_img = proc_img.convert('RGB')
            proc_img.save(file_path)
            print(f"Generated corrected TIF with orientation fixes: {os.path.basename(file_path)}")
        
        # Crop top 60px for OCR
        width, height = proc_img.size
        cropped_img = proc_img.crop((0, 60, width, height))
        config = '--oem 1 --psm 6'
        text = pytesseract.image_to_string(cropped_img, config=config, lang='eng')
        return text, orientation_corrected
    except Exception as e:
        print(f"Error processing TIF: {e}")
        return "", False

def process_document(file_path):
    """
    Process the document: move to work folder, extract text, classify the document,
    move to final folder, and return the results including final file path.
    
    NEW WORKFLOW:
    1. Move file from WATCH_DIR to WORK_DIR for processing
    2. Extract text and classify the document (now with medSpaCy integration)
    3. Move file from WORK_DIR to FINAL_DIR after successful processing
    4. Return final file path (not just basename) for database storage
    
    Returns:
        tuple: (final_file_path, document_type, extracted_text, orientation_corrected, extracted_entities)
    """
    print("PROCESS_DOCUMENT CALLED")
    work_file = move_to_work_folder(file_path)
    extracted_text = ""
    orientation_corrected = False
    
    if work_file.lower().endswith(".pdf"):
        extracted_text, orientation_corrected = extract_text_from_pdf(work_file)
    elif work_file.lower().endswith((".tif", ".tiff")):
        extracted_text, orientation_corrected = extract_text_from_tif(work_file)
    else:
        print("Unsupported file format")
    
    # Classify document and extract entities using medSpaCy when available
    document_type, extracted_entities = classify_document(work_file, extracted_text)
    
    # Move to final folder after successful processing
    final_file = move_to_final_folder(work_file)
    
    return final_file, document_type, extracted_text, orientation_corrected, extracted_entities