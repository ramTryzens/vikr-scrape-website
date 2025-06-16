#!/usr/bin/env python3
"""
Test script for web crawler functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.services.crawler_service import WebCrawler

def test_crawler():
    """Test the web crawler with a simple website"""
    
    # Test URLs (using httpbin.org for reliable testing)
    test_urls = ['https://httpbin.org/html']
    
    print("Testing web crawler...")
    print(f"Starting URLs: {test_urls}")
    
    # Initialize crawler with max depth 1 for testing
    crawler = WebCrawler(max_depth=1, delay=0.5)
    
    # Callback to track progress
    def progress_callback(page_data):
        print(f"✅ Crawled: {page_data['url']} (depth: {page_data['depth']})")
        if page_data['error_message']:
            print(f"   ❌ Error: {page_data['error_message']}")
        else:
            print(f"   📄 Title: {page_data['title'][:50]}...")
            print(f"   📝 Content length: {len(page_data['content'])} chars")
            print(f"   🎥 Videos found: {len(page_data['videos'])}")
    
    # Run crawler
    results = crawler.crawl_urls(test_urls, callback=progress_callback)
    
    print(f"\n📊 Crawling completed!")
    print(f"Total pages crawled: {len(results)}")
    print(f"URLs visited: {len(crawler.visited_urls)}")
    
    return len(results) > 0

if __name__ == '__main__':
    success = test_crawler()
    if success:
        print("\n✅ Crawler test passed!")
    else:
        print("\n❌ Crawler test failed!")

