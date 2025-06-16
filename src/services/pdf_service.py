from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import os
from typing import List, Dict

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # URL style
        self.styles.add(ParagraphStyle(
            name='URLStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='blue',
            spaceAfter=12
        ))
        
        # Content style
        self.styles.add(ParagraphStyle(
            name='ContentStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_LEFT
        ))
        
        # Video style
        self.styles.add(ParagraphStyle(
            name='VideoStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='green',
            spaceAfter=6
        ))
    
    def clean_text(self, text: str) -> str:
        """Clean text for PDF generation"""
        if not text:
            return ""
        
        # Remove or replace problematic characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        # Limit text length to prevent overly long paragraphs
        if len(text) > 5000:
            text = text[:5000] + "... [Content truncated]"
        
        return text
    
    def generate_pdf(self, crawl_data: List[Dict], output_path: str, job_info: Dict = None) -> bool:
        """Generate PDF from crawled data"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Add title page
            story.append(Paragraph("Web Crawling Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 12))
            
            if job_info:
                story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
                story.append(Paragraph(f"Total pages crawled: {len(crawl_data)}", self.styles['Normal']))
                if job_info.get('urls'):
                    story.append(Paragraph("Starting URLs:", self.styles['Heading2']))
                    for url in job_info['urls']:
                        story.append(Paragraph(f"• {url}", self.styles['URLStyle']))
                story.append(Spacer(1, 20))
            
            story.append(PageBreak())
            
            # Add content for each crawled page
            for i, page_data in enumerate(crawl_data):
                # Page header
                story.append(Paragraph(f"Page {i + 1}", self.styles['Heading1']))
                story.append(Spacer(1, 12))
                
                # URL
                story.append(Paragraph("URL:", self.styles['Heading3']))
                story.append(Paragraph(self.clean_text(page_data.get('url', '')), self.styles['URLStyle']))
                
                # Title
                if page_data.get('title'):
                    story.append(Paragraph("Title:", self.styles['Heading3']))
                    story.append(Paragraph(self.clean_text(page_data['title']), self.styles['Normal']))
                    story.append(Spacer(1, 12))
                
                # Depth
                story.append(Paragraph(f"Crawl Depth: {page_data.get('depth', 0)}", self.styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Content
                if page_data.get('content'):
                    story.append(Paragraph("Content:", self.styles['Heading3']))
                    content = self.clean_text(page_data['content'])
                    # Split long content into smaller paragraphs
                    content_chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                    for chunk in content_chunks:
                        if chunk.strip():
                            story.append(Paragraph(chunk, self.styles['ContentStyle']))
                    story.append(Spacer(1, 12))
                
                # Videos
                if page_data.get('videos') and len(page_data['videos']) > 0:
                    story.append(Paragraph("Videos Found:", self.styles['Heading3']))
                    for video_url in page_data['videos']:
                        story.append(Paragraph(f"• {self.clean_text(video_url)}", self.styles['VideoStyle']))
                    story.append(Spacer(1, 12))
                
                # Error information
                if page_data.get('error_message'):
                    story.append(Paragraph("Error:", self.styles['Heading3']))
                    story.append(Paragraph(self.clean_text(page_data['error_message']), self.styles['Normal']))
                    story.append(Spacer(1, 12))
                
                # Add page break between pages (except for the last one)
                if i < len(crawl_data) - 1:
                    story.append(PageBreak())
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return False
    
    def get_pdf_info(self, pdf_path: str) -> Dict:
        """Get information about the generated PDF"""
        try:
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                return {
                    'exists': True,
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'path': pdf_path
                }
            else:
                return {'exists': False}
        except Exception as e:
            return {'exists': False, 'error': str(e)}

