import os
import cv2
import numpy as np
import shutil
import yaml
import math
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract

# Set tesseract path based on the operating system
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:  # Unix/Linux systems
    # Use the system tesseract (should be in PATH after installation)
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

# Define your working directories here
WATCH_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_IN")    # Input folder for new documents
WORK_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_working")  # Temporary processing folder
FINAL_DIR = os.path.abspath(r"C:\PDF-Processing\PDF_final")   # Final storage for processed documents

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
        debug_base = os.path.abspath(os.path.join(r"C:\PDF-Processing", debug_base))
    
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

def preprocess_orientation_correction(img, base_name, page_idx):
    """
    Apply page orientation correction using Tesseract's OSD (Orientation and Script Detection).
    
    Args:
        img: PIL Image
        base_name: Base filename for debug images
        page_idx: Page index
        
    Returns:
        PIL Image after orientation correction
    """
    config = CONFIG.get('orientation_correction', {})
    if not config.get('enabled', True):
        return img
    
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
        if rotation_angle != 0:
            print(f"Detected {rotation_angle}° rotation, correcting orientation...")
            # Rotate counter-clockwise to correct the orientation
            corrected_img = img.rotate(-rotation_angle, expand=True, fillcolor='white')
        
        # Save corrected image
        save_debug_image(corrected_img, base_name, page_idx, 'after_orientation',
                        CONFIG.get('debug', {}).get('subfolders', {}).get('orientation'))
        
        return corrected_img
        
    except Exception as e:
        print(f"Warning: Orientation correction failed for page {page_idx}: {e}")
        # Return original image if orientation detection fails
        return img

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

def classify_document(file_path, extracted_text):
    """
    Identify and classify the document type based on the file content.
    You can start with some simple keyword matching; later you can replace this with a machine
    learning model or more complex logic.
    """
    if "invoice" in extracted_text.lower():
        return "Invoice"
    elif "receipt" in extracted_text.lower():
        return "Receipt"
    elif "report" in extracted_text.lower():
        return "Report"
    else:
        return "Unknown"

def preprocess_fax_page(pil_img, base_name="image", page_idx=0):
    """
    Preprocess a PIL image of a fax PDF page for improved OCR accuracy.
    Now uses modular preprocessing steps that can be configured.
    
    Args:
        pil_img: PIL Image to preprocess
        base_name: Base filename for debug images
        page_idx: Page index for debug images
        
    Returns:
        PIL Image after all enabled preprocessing steps
    """
    # Apply preprocessing steps in order
    img = preprocess_orientation_correction(pil_img, base_name, page_idx)
    img = preprocess_basic(img, base_name, page_idx)
    img = preprocess_noise_removal(img, base_name, page_idx)
    img = preprocess_morphological_operations(img, base_name, page_idx)
    img = preprocess_line_removal(img, base_name, page_idx)
    
    return img

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF, using preprocessing optimized for faxed documents.
    Saves debug images with original filename as prefix.
    Skips extraction of the top 60px of each page.
    """
    debug_folder = r"C:\PDF-Processing\debug_imgs"
    os.makedirs(debug_folder, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    try:
        # Use higher DPI for faxes
        pages = convert_from_path(
            file_path, 
            dpi=400, 
            poppler_path=r"C:\PDF-Processing\poppler\Library\bin"
        )
        text = ""
        for i, page in enumerate(pages):
            # Preprocessing step here with base_name and page index:
            proc_page = preprocess_fax_page(page, base_name, i)
            
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
        return text
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return ""

def extract_text_from_tif(file_path):
    """
    Use OCR to extract text from a TIF, skipping the top 60px.
    """
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    try:
        img = Image.open(file_path)
        proc_img = preprocess_fax_page(img, base_name, 0)
        # Crop top 60px
        width, height = proc_img.size
        cropped_img = proc_img.crop((0, 60, width, height))
        config = '--oem 1 --psm 6'
        text = pytesseract.image_to_string(cropped_img, config=config, lang='eng')
        return text
    except Exception as e:
        print(f"Error processing TIF: {e}")
        return ""

def process_document(file_path):
    """
    Process the document: move to work folder, extract text, classify the document,
    move to final folder, and return the results including final file path.
    
    NEW WORKFLOW:
    1. Move file from WATCH_DIR to WORK_DIR for processing
    2. Extract text and classify the document
    3. Move file from WORK_DIR to FINAL_DIR after successful processing
    4. Return final file path (not just basename) for database storage
    """
    print("PROCESS_DOCUMENT CALLED")
    work_file = move_to_work_folder(file_path)
    extracted_text = ""
    if work_file.lower().endswith(".pdf"):
        extracted_text = extract_text_from_pdf(work_file)
    elif work_file.lower().endswith((".tif", ".tiff")):
        extracted_text = extract_text_from_tif(work_file)
    else:
        print("Unsupported file format")
    
    document_type = classify_document(work_file, extracted_text)
    
    # Move to final folder after successful processing
    final_file = move_to_final_folder(work_file)
    
    return final_file, document_type, extracted_text