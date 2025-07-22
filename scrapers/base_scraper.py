"""
فئة أساسية لاستخراج المحتوى من مواقع الويب
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
from typing import Dict, List, Optional
import re


class BaseScraper:
    """فئة أساسية لاستخراج المحتوى من مواقع الويب"""
    
    def __init__(self, delay: float = 1.0):
        """
        تهيئة الفئة الأساسية
        
        Args:
            delay: التأخير بين الطلبات بالثواني
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        جلب صفحة ويب وتحويلها إلى BeautifulSoup
        
        Args:
            url: رابط الصفحة
            
        Returns:
            كائن BeautifulSoup أو None في حالة الفشل
        """
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # تحديد الترميز
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
            
        except Exception as e:
            print(f"خطأ في جلب الصفحة {url}: {e}")
            return None
    
    def extract_text(self, element) -> str:
        """استخراج النص من عنصر HTML مع تنظيفه"""
        if not element:
            return ""
        
        text = element.get_text(strip=True)
        # تنظيف النص من المسافات الزائدة
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """استخراج جميع الروابط من الصفحة"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            if self.is_valid_url(full_url):
                links.append(full_url)
        return links
    
    def is_valid_url(self, url: str) -> bool:
        """التحقق من صحة الرابط"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """استخراج روابط الصور من الصفحة"""
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            full_url = urljoin(base_url, src)
            if self.is_valid_url(full_url):
                images.append(full_url)
        return images
    
    def extract_meta_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """استخراج البيانات الوصفية من الصفحة"""
        meta_data = {}
        
        # استخراج العنوان
        title_tag = soup.find('title')
        if title_tag:
            meta_data['title'] = self.extract_text(title_tag)
        
        # استخراج الوصف
        description_tag = soup.find('meta', attrs={'name': 'description'})
        if description_tag and description_tag.get('content'):
            meta_data['description'] = description_tag['content']
        
        # استخراج الكلمات المفتاحية
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            meta_data['keywords'] = keywords_tag['content']
        
        # استخراج بيانات Open Graph
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            if property_name and content:
                meta_data[f'og_{property_name}'] = content
        
        return meta_data
    
    def extract_article_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        """استخراج محتوى المقال من الصفحة"""
        content = {}
        
        # البحث عن المحتوى الرئيسي
        main_content = None
        
        # محاولة العثور على المحتوى باستخدام علامات شائعة
        selectors = [
            'article',
            '.post-content',
            '.entry-content',
            '.content',
            '.main-content',
            '#content',
            '.article-body',
            '.post-body'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                main_content = element
                break
        
        # إذا لم نجد محتوى محدد، نأخذ النص من body
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # إزالة العناصر غير المرغوب فيها
            for unwanted in main_content.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                unwanted.decompose()
            
            content['text'] = self.extract_text(main_content)
            
            # استخراج الفقرات
            paragraphs = main_content.find_all('p')
            content['paragraphs'] = [self.extract_text(p) for p in paragraphs if self.extract_text(p)]
        
        return content
    
    def get_domain(self, url: str) -> str:
        """استخراج اسم النطاق من الرابط"""
        try:
            return urlparse(url).netloc
        except:
            return ""
    
    def scrape_generic_page(self, url: str) -> Dict:
        """
        استخراج المحتوى العام من أي صفحة ويب
        
        Args:
            url: رابط الصفحة
            
        Returns:
            قاموس يحتوي على المحتوى المستخرج
        """
        soup = self.get_page(url)
        if not soup:
            return {}
        
        result = {
            'url': url,
            'domain': self.get_domain(url),
            'scraped_at': datetime.now().isoformat(),
            'meta_data': self.extract_meta_data(soup),
            'content': self.extract_article_content(soup),
            'images': self.extract_images(soup, url),
            'links': self.extract_links(soup, url)[:10]  # أول 10 روابط فقط
        }
        
        return result

