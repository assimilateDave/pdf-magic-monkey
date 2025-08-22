#!/usr/bin/env python3
"""
Test script for PDF orientation correction functionality.
This script tests the enhanced PDF processing pipeline.
"""

import os
import tempfile
import shutil
from PIL import Image
import sys

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processor import extract_text_from_pdf, process_document, WORK_DIR, FINAL_DIR

def create_test_pdf():
    """
    Create a simple test PDF with rotated content for testing.
    Returns path to the created test PDF.
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a simple image with text
    width, height = 400, 300
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw some text (this will be readable when properly oriented)
    try:
        # Try to use default font, fall back to built-in if not available
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((50, 100), "Test Document", fill='black', font=font)
    draw.text((50, 150), "Page 1 - Normal orientation", fill='black', font=font)
    draw.rectangle([50, 200, 350, 250], outline='black', width=2)
    
    # Rotate the image 90 degrees to simulate incorrect orientation
    rotated_img = img.rotate(90, expand=True)
    
    # Save as PDF
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "test_rotated.pdf")
    rotated_img.save(pdf_path, "PDF")
    
    print(f"Created test PDF: {pdf_path}")
    return pdf_path

def create_test_pdf_with_text():
    """
    Create a test PDF with clear text content that should trigger orientation detection.
    Returns path to the created test PDF.
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a simple image with clear, readable text
    width, height = 400, 300
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw clear text that OCR can recognize
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((50, 50), "TEST DOCUMENT", fill='black', font=font)
    draw.text((50, 100), "This is page one", fill='black', font=font) 
    draw.text((50, 150), "Normal orientation", fill='black', font=font)
    draw.text((50, 200), "Should be readable", fill='black', font=font)
    
    # Add more clear geometric shapes for better OCR detection
    draw.rectangle([30, 30, 370, 270], outline='black', width=3)
    draw.rectangle([60, 250, 200, 280], fill='black')
    draw.text((65, 255), "Black Box", fill='white', font=font)
    
    # Create a 90-degree rotated version (this should trigger correction)
    rotated_img = img.rotate(90, expand=True, fillcolor='white')
    
    # Save as PDF
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "test_rotated_with_text.pdf")
    rotated_img.save(pdf_path, "PDF")
    
    print(f"Created test PDF with text: {pdf_path}")
    return pdf_path

def create_test_pdf_normal():
    """
    Create a test PDF with normal orientation (no correction needed).
    Returns path to the created test PDF.
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a simple image with clear, readable text (normal orientation)
    width, height = 400, 300
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw clear text that OCR can recognize
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((50, 50), "TEST DOCUMENT", fill='black', font=font)
    draw.text((50, 100), "This is page one", fill='black', font=font) 
    draw.text((50, 150), "Normal orientation", fill='black', font=font)
    draw.text((50, 200), "Should be readable", fill='black', font=font)
    
    # Add more clear geometric shapes for better OCR detection
    draw.rectangle([30, 30, 370, 270], outline='black', width=3)
    draw.rectangle([60, 250, 200, 280], fill='black')
    draw.text((65, 255), "Black Box", fill='white', font=font)
    
    # NO rotation - keep normal orientation
    
    # Save as PDF
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "test_normal.pdf")
    img.save(pdf_path, "PDF")
    
    print(f"Created normal test PDF: {pdf_path}")
    return pdf_path

def test_normal_orientation():
    """Test behavior when no orientation correction is needed."""
    print("\n=== Testing Normal Orientation (No Correction Needed) ===")
    
    # Create test directories if they don't exist
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    # Create test PDF with normal orientation
    test_pdf = create_test_pdf_normal()
    
    try:
        print("\n1. Testing normal orientation processing...")
        
        # Copy to work directory to simulate the workflow
        work_pdf = os.path.join(WORK_DIR, "test_normal.pdf")
        shutil.copy2(test_pdf, work_pdf)
        
        # Get file size before processing
        size_before = os.path.getsize(work_pdf)
        print(f"   File size before processing: {size_before} bytes")
        
        # Extract text and check orientation correction status
        extracted_text, orientation_corrected = extract_text_from_pdf(work_pdf)
        
        # Get file size after processing (should be the same for normal orientation)
        size_after = os.path.getsize(work_pdf) 
        print(f"   File size after processing: {size_after} bytes")
        print(f"   File size changed: {size_before != size_after}")
        
        print(f"   Extracted text length: {len(extracted_text)}")
        print(f"   Orientation corrected: {orientation_corrected}")
        print(f"   Text preview: {repr(extracted_text[:100])}" if extracted_text else "   No text extracted")
        
        # The file should be unchanged if no orientation correction occurred
        if not orientation_corrected:
            print("   ✅ File correctly left unchanged (no orientation correction needed)")
        else:
            print("   ❌ File was changed when no correction should be needed")
        
        # Clean up work file
        if os.path.exists(work_pdf):
            os.remove(work_pdf)
            
    except Exception as e:
        print(f"   Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test PDF
        shutil.rmtree(os.path.dirname(test_pdf), ignore_errors=True)

def test_enhanced_behavior():
    """Test the enhanced PDF processing behavior with orientation correction."""
    print("\n=== Testing Enhanced PDF Processing with Orientation Correction ===")
    
    # Create test directories if they don't exist
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    # Create test PDF with clear text
    test_pdf = create_test_pdf_with_text()
    
    try:
        print("\n1. Testing enhanced extract_text_from_pdf()...")
        
        # Copy to work directory to simulate the workflow
        work_pdf = os.path.join(WORK_DIR, "test_rotated_with_text.pdf")
        shutil.copy2(test_pdf, work_pdf)
        
        # Get file size before processing
        size_before = os.path.getsize(work_pdf)
        print(f"   File size before processing: {size_before} bytes")
        
        # Extract text and check orientation correction status
        extracted_text, orientation_corrected = extract_text_from_pdf(work_pdf)
        
        # Get file size after processing (might be different if corrected PDF was generated)
        size_after = os.path.getsize(work_pdf) 
        print(f"   File size after processing: {size_after} bytes")
        print(f"   File size changed: {size_before != size_after}")
        
        print(f"   Extracted text length: {len(extracted_text)}")
        print(f"   Orientation corrected: {orientation_corrected}")
        print(f"   Text preview: {repr(extracted_text[:100])}" if extracted_text else "   No text extracted")
        
        # Test that we can still read the processed PDF
        try:
            from pdf2image import convert_from_path
            test_pages = convert_from_path(work_pdf, dpi=200)
            print(f"   Corrected PDF has {len(test_pages)} pages")
        except Exception as e:
            print(f"   Error reading corrected PDF: {e}")
        
        # Clean up work file
        if os.path.exists(work_pdf):
            os.remove(work_pdf)
            
    except Exception as e:
        print(f"   Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test PDF
        shutil.rmtree(os.path.dirname(test_pdf), ignore_errors=True)

def test_enhanced_behavior():
    """Test the complete process_document workflow."""
    print("\n=== Testing Complete process_document Workflow ===")
    
    # Create test directories if they don't exist 
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    # Create test PDF
    test_pdf = create_test_pdf_with_text()
    
    try:
        # Move to watch directory (simulate file drop)
        watch_pdf = os.path.join("/tmp", "test_input.pdf")
        shutil.copy2(test_pdf, watch_pdf)
        
        print(f"   Processing file: {watch_pdf}")
        
        # Process the document
        final_file, doc_type, extracted_text, orientation_corrected, extracted_entities = process_document(watch_pdf)
        
        print(f"   Final file: {final_file}")
        print(f"   Document type: {doc_type}")
        print(f"   Text length: {len(extracted_text)}")
        print(f"   Orientation corrected: {orientation_corrected}")
        print(f"   Final file exists: {os.path.exists(final_file)}")
        
        # Verify final file is readable
        if os.path.exists(final_file):
            final_size = os.path.getsize(final_file)
            print(f"   Final file size: {final_size} bytes")
            
        # Clean up
        if os.path.exists(final_file):
            os.remove(final_file)
        
    except Exception as e:
        print(f"   Error during workflow test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test PDF
        shutil.rmtree(os.path.dirname(test_pdf), ignore_errors=True)

def test_pdf_creation():
    """Test creating PDF from PIL images."""
    print("\n=== Testing PDF Creation from PIL Images ===")
    
    try:
        from PIL import ImageDraw, ImageFont
        
        # Create test images
        images = []
        for i in range(3):
            img = Image.new('RGB', (400, 300), color='white')
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            draw.text((50, 100 + i*50), f"Page {i+1}", fill='black', font=font)
            draw.text((50, 150 + i*50), "Test content", fill='black', font=font)
            images.append(img)
        
        # Save as PDF
        temp_dir = tempfile.mkdtemp()
        output_pdf = os.path.join(temp_dir, "test_output.pdf")
        
        # Use Pillow to create multi-page PDF
        if images:
            images[0].save(output_pdf, "PDF", save_all=True, append_images=images[1:])
            print(f"   Successfully created PDF: {output_pdf}")
            print(f"   PDF file size: {os.path.getsize(output_pdf)} bytes")
        
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"   Error creating PDF: {e}")

def test_full_workflow():
    """Test the complete process_document workflow."""
    print("\n=== Testing Complete process_document Workflow ===")
    
    # Create test directories if they don't exist 
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    # Create test PDF
    test_pdf = create_test_pdf_with_text()
    
    try:
        # Move to watch directory (simulate file drop)
        watch_pdf = os.path.join("/tmp", "test_input.pdf")
        shutil.copy2(test_pdf, watch_pdf)
        
        print(f"   Processing file: {watch_pdf}")
        
        # Process the document
        final_file, doc_type, extracted_text, orientation_corrected, extracted_entities = process_document(watch_pdf)
        
        print(f"   Final file: {final_file}")
        print(f"   Document type: {doc_type}")
        print(f"   Text length: {len(extracted_text)}")
        print(f"   Orientation corrected: {orientation_corrected}")
        print(f"   Final file exists: {os.path.exists(final_file)}")
        
        # Verify final file is readable
        if os.path.exists(final_file):
            final_size = os.path.getsize(final_file)
            print(f"   Final file size: {final_size} bytes")
            
        # Clean up
        if os.path.exists(final_file):
            os.remove(final_file)
        
    except Exception as e:
        print(f"   Error during workflow test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test PDF
        shutil.rmtree(os.path.dirname(test_pdf), ignore_errors=True)

if __name__ == "__main__":
    print("PDF Orientation Correction Test Suite")
    print("=" * 50)
    
    test_normal_orientation()
    test_enhanced_behavior() 
    test_pdf_creation()
    test_full_workflow()
    
    print("\n=== Test Complete ===")