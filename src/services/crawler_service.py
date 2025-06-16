import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import re
from typing import List, Set, Dict, Tuple
from datetime import datetime

class WebCrawler:
    def __init__(self, max_depth: int = 3, delay: float = 1.0):
        self.max_depth = max_depth
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and should be crawled"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ['http', 'https']
        except:
            return False
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and query parameters"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    def extract_content(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Extract text content and videos from HTML"""
        # Extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text content
        text_content = soup.get_text()
        # Clean up text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Extract video URLs
        videos = []
        
        # Find video tags
        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src')
            if src:
                videos.append(src)
            # Check for source tags within video
            sources = video.find_all('source')
            for source in sources:
                src = source.get('src')
                if src:
                    videos.append(src)
        
        # Find iframe embeds (YouTube, Vimeo, etc.)
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if any(domain in src for domain in ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com']):
                videos.append(src)
        
        # Find links to video files
        links = soup.find_all('a')
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
        for link in links:
            href = link.get('href', '')
            if any(ext in href.lower() for ext in video_extensions):
                videos.append(href)
        
        return {
            'title': title,
            'content': content,
            'videos': list(set(videos))  # Remove duplicates
        }
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            normalized_url = self.normalize_url(full_url)
            if self.is_valid_url(normalized_url):
                links.append(normalized_url)
        return list(set(links))  # Remove duplicates
    
    def crawl_page(self, url: str) -> Tuple[Dict[str, any], List[str]]:
        """Crawl a single page and return content and links"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            content = self.extract_content(soup)
            links = self.extract_links(soup, url)
            
            return {
                'url': url,
                'title': content['title'],
                'content': content['content'],
                'videos': content['videos'],
                'status_code': response.status_code,
                'error_message': None
            }, links
            
        except requests.RequestException as e:
            return {
                'url': url,
                'title': '',
                'content': '',
                'videos': [],
                'status_code': getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0,
                'error_message': str(e)
            }, []
        except Exception as e:
            return {
                'url': url,
                'title': '',
                'content': '',
                'videos': [],
                'status_code': 0,
                'error_message': str(e)
            }, []
    
    def crawl_urls(self, start_urls: List[str], callback=None) -> List[Dict[str, any]]:
        """Crawl multiple URLs with depth control"""
        results = []
        urls_to_crawl = [(url, 0) for url in start_urls]  # (url, depth)
        
        while urls_to_crawl:
            current_url, depth = urls_to_crawl.pop(0)
            
            # Skip if already visited or depth exceeded
            if current_url in self.visited_urls or depth > self.max_depth:
                continue
            
            self.visited_urls.add(current_url)
            
            # Crawl the page
            page_data, links = self.crawl_page(current_url)
            page_data['depth'] = depth
            results.append(page_data)
            
            # Call callback if provided (for progress updates)
            if callback:
                callback(page_data)
            
            # Add new links to crawl queue if within depth limit
            if depth < self.max_depth:
                for link in links:
                    if link not in self.visited_urls:
                        urls_to_crawl.append((link, depth + 1))
            
            # Add delay between requests
            time.sleep(self.delay)
        
        return results

