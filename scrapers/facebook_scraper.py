"""
وحدة استخراج المحتوى من فيسبوك
"""

from facebook_scraper import get_posts, get_profile
from .base_scraper import BaseScraper
from datetime import datetime
from typing import Dict, List, Optional
import re
from urllib.parse import urlparse


class FacebookScraper(BaseScraper):
    """فئة استخراج المحتوى من فيسبوك"""
    
    def __init__(self, delay: float = 2.0):
        """
        تهيئة فئة فيسبوك
        
        Args:
            delay: التأخير بين الطلبات بالثواني
        """
        super().__init__(delay)
        self.platform = "Facebook"
    
    def extract_page_name_from_url(self, url: str) -> Optional[str]:
        """
        استخراج اسم الصفحة من رابط فيسبوك
        
        Args:
            url: رابط صفحة فيسبوك
            
        Returns:
            اسم الصفحة أو None
        """
        try:
            # أنماط مختلفة لروابط فيسبوك
            patterns = [
                r'facebook\.com/([^/?]+)',
                r'facebook\.com/pages/[^/]+/(\d+)',
                r'facebook\.com/profile\.php\?id=(\d+)',
                r'fb\.com/([^/?]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    page_name = match.group(1)
                    # تنظيف اسم الصفحة
                    page_name = page_name.split('?')[0]  # إزالة المعاملات
                    return page_name
            
            return None
            
        except Exception as e:
            print(f"خطأ في استخراج اسم الصفحة: {e}")
            return None
    
    def scrape_facebook_page(self, url: str, max_posts: int = 10) -> Dict:
        """
        استخراج المحتوى من صفحة فيسبوك
        
        Args:
            url: رابط صفحة فيسبوك
            max_posts: عدد المنشورات المطلوب استخراجها
            
        Returns:
            قاموس يحتوي على معلومات الصفحة والمنشورات
        """
        page_name = self.extract_page_name_from_url(url)
        if not page_name:
            return {'error': 'لا يمكن استخراج اسم الصفحة من الرابط'}
        
        try:
            # استخراج معلومات الصفحة
            profile_info = {}
            try:
                profile_info = get_profile(page_name)
            except Exception as e:
                print(f"تعذر الحصول على معلومات الصفحة: {e}")
            
            # استخراج المنشورات
            posts = []
            post_count = 0
            
            try:
                for post in get_posts(page_name, pages=3):
                    if post_count >= max_posts:
                        break
                    
                    processed_post = self.process_facebook_post(post)
                    if processed_post:
                        posts.append(processed_post)
                        post_count += 1
                        
            except Exception as e:
                print(f"خطأ في استخراج المنشورات: {e}")
            
            result = {
                'platform': self.platform,
                'page_name': page_name,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'profile_info': profile_info,
                'posts': posts,
                'total_posts': len(posts)
            }
            
            return result
            
        except Exception as e:
            return {'error': f'خطأ في استخراج المحتوى: {str(e)}'}
    
    def process_facebook_post(self, post: Dict) -> Optional[Dict]:
        """
        معالجة منشور فيسبوك واستخراج المعلومات المهمة
        
        Args:
            post: بيانات المنشور الخام
            
        Returns:
            منشور معالج أو None
        """
        try:
            processed = {
                'id': post.get('post_id', ''),
                'text': post.get('text', ''),
                'time': self.format_datetime(post.get('time')),
                'likes': post.get('likes', 0),
                'comments': post.get('comments', 0),
                'shares': post.get('shares', 0),
                'post_url': post.get('post_url', ''),
                'images': post.get('images', []),
                'video': post.get('video', ''),
                'link': post.get('link', ''),
                'reactions': post.get('reactions', {}),
                'username': post.get('username', ''),
                'user_id': post.get('user_id', '')
            }
            
            # تنظيف النص
            if processed['text']:
                processed['text'] = self.clean_text(processed['text'])
            
            # إضافة ملخص قصير
            if processed['text']:
                processed['summary'] = self.create_summary(processed['text'])
            
            return processed
            
        except Exception as e:
            print(f"خطأ في معالجة المنشور: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """تنظيف النص من الأحرف غير المرغوب فيها"""
        if not text:
            return ""
        
        # إزالة الروابط
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # تنظيف المسافات الزائدة
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def create_summary(self, text: str, max_length: int = 150) -> str:
        """إنشاء ملخص قصير للنص"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # قطع النص عند أول نقطة أو فاصلة بعد الحد الأدنى
        min_length = max_length // 2
        
        for i in range(min_length, min(len(text), max_length)):
            if text[i] in '.!?':
                return text[:i+1].strip()
        
        # إذا لم نجد نقطة، نقطع عند آخر مسافة
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > min_length:
            return truncated[:last_space] + "..."
        
        return truncated + "..."
    
    def format_datetime(self, dt) -> str:
        """تنسيق التاريخ والوقت"""
        if not dt:
            return ""
        
        try:
            if isinstance(dt, str):
                return dt
            return dt.isoformat()
        except:
            return str(dt)
    
    def get_page_info(self, url: str) -> Dict:
        """
        الحصول على معلومات الصفحة فقط دون المنشورات
        
        Args:
            url: رابط صفحة فيسبوك
            
        Returns:
            معلومات الصفحة
        """
        page_name = self.extract_page_name_from_url(url)
        if not page_name:
            return {'error': 'لا يمكن استخراج اسم الصفحة من الرابط'}
        
        try:
            profile_info = get_profile(page_name)
            
            result = {
                'platform': self.platform,
                'page_name': page_name,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'profile_info': profile_info
            }
            
            return result
            
        except Exception as e:
            return {'error': f'خطأ في الحصول على معلومات الصفحة: {str(e)}'}
    
    def is_facebook_url(self, url: str) -> bool:
        """التحقق من أن الرابط ينتمي لفيسبوك"""
        try:
            domain = urlparse(url).netloc.lower()
            return 'facebook.com' in domain or 'fb.com' in domain
        except:
            return False

