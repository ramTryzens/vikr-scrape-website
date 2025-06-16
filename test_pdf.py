#!/usr/bin/env python3
"""
Test script for PDF generation functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.services.pdf_service import PDFGenerator

def test_pdf_generation():
    """Test the PDF generation with sample data"""
    
    # Sample crawled data
    sample_data = [
        {
            'url': 'https://example.com',
            'title': 'Example Website',
            'content': 'This is sample content from the example website. It contains various information about web development and best practices.',
            'videos': ['https://example.com/video1.mp4', 'https://youtube.com/watch?v=abc123'],
            'depth': 0,
            'status_code': 200,
            'error_message': None
        },
        {
            'url': 'https://example.com/about',
            'title': 'About Us - Example',
            'content': 'This is the about page content. It describes the company mission and values.',
            'videos': [],
            'depth': 1,
            'status_code': 200,
            'error_message': None
        },
        {
            'url': 'https://broken-link.com',
            'title': '',
            'content': '',
            'videos': [],
            'depth': 1,
            'status_code': 0,
            'error_message': 'Connection timeout'
        }
    ]
    
    # Job info
    job_info = {
        'urls': ['https://example.com'],
        'max_depth': 3,
        'total_pages': len(sample_data)
    }
    
    # Generate PDF
    pdf_generator = PDFGenerator()
    output_path = '/home/ubuntu/test_report.pdf'
    
    print("Generating test PDF...")
    success = pdf_generator.generate_pdf(sample_data, output_path, job_info)
    
    if success:
        print(f"✅ PDF generated successfully: {output_path}")
        
        # Get PDF info
        pdf_info = pdf_generator.get_pdf_info(output_path)
        print(f"📄 PDF size: {pdf_info.get('size_mb', 0)} MB")
        
        return True
    else:
        print("❌ PDF generation failed")
        return False

if __name__ == '__main__':
    test_pdf_generation()

