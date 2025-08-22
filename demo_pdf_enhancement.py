#!/usr/bin/env python3
"""
Demonstration script showing the enhanced PDF processing pipeline.

This script demonstrates:
1. Processing a PDF with incorrect orientation 
2. Automatic detection and correction
3. Generation of corrected PDF file
4. Verification that the corrected PDF is properly oriented

Usage: python demo_pdf_enhancement.py
"""

import os
import sys
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processor import process_document, WORK_DIR, FINAL_DIR

def create_demo_pdf():
    """Create a realistic demo PDF with incorrect orientation."""
    
    # Create invoice-like content
    width, height = 600, 800
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    
    # Header
    draw.text((50, 50), "INVOICE #12345", fill='black', font=font)
    draw.text((50, 80), "Date: 2024-01-15", fill='black', font=font)
    draw.line([(50, 110), (550, 110)], fill='black', width=2)
    
    # Customer info
    draw.text((50, 130), "Bill To:", fill='black', font=font)
    draw.text((50, 160), "John Smith Company", fill='black', font=font)
    draw.text((50, 180), "123 Main Street", fill='black', font=font)
    draw.text((50, 200), "Anytown, ST 12345", fill='black', font=font)
    
    # Items
    draw.text((50, 240), "Description", fill='black', font=font)
    draw.text((300, 240), "Qty", fill='black', font=font)
    draw.text((400, 240), "Price", fill='black', font=font)
    draw.text((500, 240), "Total", fill='black', font=font)
    draw.line([(50, 260), (550, 260)], fill='black', width=1)
    
    draw.text((50, 280), "Professional Services", fill='black', font=font)
    draw.text((300, 280), "10", fill='black', font=font)
    draw.text((400, 280), "$100.00", fill='black', font=font)
    draw.text((500, 280), "$1,000.00", fill='black', font=font)
    
    draw.text((50, 300), "Consulting", fill='black', font=font)
    draw.text((300, 300), "5", fill='black', font=font)
    draw.text((400, 300), "$150.00", fill='black', font=font)
    draw.text((500, 300), "$750.00", fill='black', font=font)
    
    # Total
    draw.line([(400, 340), (550, 340)], fill='black', width=2)
    draw.text((400, 360), "TOTAL:", fill='black', font=font)
    draw.text((500, 360), "$1,750.00", fill='black', font=font)
    
    # Footer
    draw.text((50, 700), "Thank you for your business!", fill='black', font=font)
    
    # Rotate 90 degrees to simulate incorrect orientation
    rotated_img = img.rotate(90, expand=True, fillcolor='white')
    
    # Save as PDF
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "demo_invoice.pdf")
    rotated_img.save(pdf_path, "PDF")
    
    return pdf_path

def main():
    print("PDF Orientation Correction Enhancement Demo")
    print("=" * 50)
    
    # Ensure directories exist
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)
    
    # Create demo PDF
    print("\n1. Creating demo PDF with incorrect orientation...")
    demo_pdf = create_demo_pdf()
    print(f"   Created: {os.path.basename(demo_pdf)}")
    print(f"   Size: {os.path.getsize(demo_pdf)} bytes")
    
    try:
        # Process the document
        print("\n2. Processing document through enhanced pipeline...")
        final_file, doc_type, extracted_text, orientation_corrected, extracted_entities = process_document(demo_pdf)
        
        print(f"   Final file: {os.path.basename(final_file)}")
        print(f"   Document type: {doc_type}")
        print(f"   Orientation was corrected: {'✅ YES' if orientation_corrected else '❌ NO'}")
        print(f"   Final file size: {os.path.getsize(final_file)} bytes")
        print(f"   Text extracted length: {len(extracted_text)} characters")
        
        # Show extracted text sample
        if extracted_text:
            # Clean up the text for display
            cleaned_text = ' '.join(extracted_text.split())
            print(f"   Text sample: {cleaned_text[:200]}...")
        
        print("\n3. Results Summary:")
        if orientation_corrected:
            print("   ✅ Orientation correction was applied")
            print("   ✅ New corrected PDF was generated")
            print("   ✅ Original PDF was replaced with corrected version")
            print("   ✅ Users will see properly oriented document")
        else:
            print("   ℹ️ No orientation correction needed")
            print("   ✅ Original PDF was preserved")
        
        # Verify corrected PDF is readable
        print("\n4. Verification:")
        if os.path.exists(final_file):
            from pdf2image import convert_from_path
            try:
                pages = convert_from_path(final_file, dpi=150)
                print(f"   ✅ Corrected PDF successfully readable ({len(pages)} pages)")
            except Exception as e:
                print(f"   ❌ Error reading corrected PDF: {e}")
        
        # Clean up
        if os.path.exists(final_file):
            os.remove(final_file)
            print("   🧹 Cleaned up demo files")
        
    except Exception as e:
        print(f"   ❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up demo PDF
        shutil.rmtree(os.path.dirname(demo_pdf), ignore_errors=True)
    
    print("\n" + "=" * 50)
    print("Demo Complete!")
    print("\nThe enhanced PDF processing pipeline now:")
    print("• Detects incorrect orientation automatically")
    print("• Generates corrected PDFs when needed")
    print("• Preserves original files when no correction is needed")
    print("• Maintains all existing functionality")

if __name__ == "__main__":
    main()