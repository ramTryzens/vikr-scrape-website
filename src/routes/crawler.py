from flask import Blueprint, jsonify, request, send_file, current_app
from src.models.crawler import CrawlJob, CrawledPage, db
from src.services.crawler_service import WebCrawler
from src.services.pdf_service import PDFGenerator
import json
import os
import threading
from datetime import datetime
import uuid

crawler_bp = Blueprint('crawler', __name__)

def run_crawl_job(app, job_id: int):
    """Background function to run the crawl job"""
    with app.app_context():  # ✅ this line adds context to the thread
        try:
            job = CrawlJob.query.get(job_id)
            if not job:
                return

            job.status = 'running'
            db.session.commit()

            urls = json.loads(job.urls)
            crawler = WebCrawler(max_depth=job.max_depth)

            def save_page_callback(page_data):
                try:
                    crawled_page = CrawledPage(
                        job_id=job.id,
                        url=page_data['url'],
                        title=page_data['title'],
                        content=page_data['content'],
                        videos=json.dumps(page_data['videos']),
                        depth=page_data['depth'],
                        status_code=page_data['status_code'],
                        error_message=page_data['error_message']
                    )
                    db.session.add(crawled_page)
                    db.session.commit()

                    job.total_pages = CrawledPage.query.filter_by(job_id=job.id).count()
                    db.session.commit()

                except Exception as e:
                    print(f"Error saving page: {str(e)}")

            results = crawler.crawl_urls(urls, callback=save_page_callback)

            pdf_generator = PDFGenerator()
            pdf_filename = f"crawl_report_{job.id}_{uuid.uuid4().hex[:8]}.pdf"
            pdf_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'pdfs', pdf_filename)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

            job_info = {
                'urls': urls,
                'max_depth': job.max_depth,
                'total_pages': len(results)
            }

            pdf_success = pdf_generator.generate_pdf(results, pdf_path, job_info)

            if pdf_success:
                job.pdf_filename = pdf_filename
                job.status = 'completed'
            else:
                job.status = 'failed'
                job.error_message = 'Failed to generate PDF'

            job.completed_at = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            job = CrawlJob.query.get(job_id)
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.session.commit()

@crawler_bp.route('/crawl', methods=['POST'])
def start_crawl():
    """Start a new crawl job"""
    try:
        data = request.json

        if not data or 'urls' not in data:
            return jsonify({'error': 'URLs are required'}), 400

        urls = data['urls']
        if not isinstance(urls, list) or len(urls) == 0:
            return jsonify({'error': 'URLs must be a non-empty list'}), 400

        max_depth = data.get('max_depth', 3)
        if max_depth < 0 or max_depth > 5:
            return jsonify({'error': 'Max depth must be between 0 and 5'}), 400

        # Create new crawl job
        job = CrawlJob(
            urls=json.dumps(urls),
            max_depth=max_depth,
            status='pending'
        )

        db.session.add(job)
        db.session.commit()

        # Start crawling in background thread
        # thread = threading.Thread(target=run_crawl_job, args=(job.id,))
        thread = threading.Thread(target=run_crawl_job, args=(current_app._get_current_object(), job.id))
        thread.daemon = True
        thread.start()

        return jsonify({
            'message': 'Crawl job started successfully',
            'job_id': job.id,
            'status': job.status
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@crawler_bp.route('/jobs', methods=['GET'])
def get_jobs():
    """Get all crawl jobs"""
    try:
        jobs = CrawlJob.query.order_by(CrawlJob.created_at.desc()).all()
        return jsonify([job.to_dict() for job in jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@crawler_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get a specific crawl job"""
    try:
        job = CrawlJob.query.get_or_404(job_id)
        return jsonify(job.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@crawler_bp.route('/jobs/<int:job_id>/pages', methods=['GET'])
def get_job_pages(job_id):
    """Get all pages for a specific job"""
    try:
        job = CrawlJob.query.get_or_404(job_id)
        pages = CrawledPage.query.filter_by(job_id=job_id).order_by(CrawledPage.depth, CrawledPage.crawled_at).all()
        return jsonify([page.to_dict() for page in pages])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@crawler_bp.route('/jobs/<int:job_id>/download', methods=['GET'])
def download_pdf(job_id):
    """Download the PDF report for a job"""
    try:
        job = CrawlJob.query.get_or_404(job_id)
        
        if job.status != 'completed' or not job.pdf_filename:
            return jsonify({'error': 'PDF not available. Job may not be completed or may have failed.'}), 400
        
        pdf_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'pdfs', job.pdf_filename)
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF file not found'}), 404
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"crawl_report_{job_id}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@crawler_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a crawl job and its associated data"""
    try:
        job = CrawlJob.query.get_or_404(job_id)
        
        # Delete PDF file if it exists
        if job.pdf_filename:
            pdf_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'pdfs', job.pdf_filename)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        
        # Delete job (pages will be deleted automatically due to cascade)
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({'message': 'Job deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
