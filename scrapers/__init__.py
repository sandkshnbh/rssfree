"""
حزمة أدوات استخراج المحتوى من منصات التواصل الاجتماعي
"""

from .base_scraper import BaseScraper
from .facebook_scraper import FacebookScraper
from .instagram_scraper import InstagramScraper

__all__ = ['BaseScraper', 'FacebookScraper', 'InstagramScraper']

