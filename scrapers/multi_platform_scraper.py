"""
وحدة دعم منصات متعددة للتواصل الاجتماعي
"""

from .base_scraper import BaseScraper
from .facebook_scraper import FacebookScraper
from .instagram_scraper import InstagramScraper
from datetime import datetime
from typing import Dict, List, Optional
import re
from urllib.parse import urlparse
import json


class MultiPlatformScraper(BaseScraper):
    """فئة دعم منصات متعددة"""
    
    def __init__(self, delay: float = 2.0):
        """
        تهيئة فئة المنصات المتعددة
        
        Args:
            delay: التأخير بين الطلبات بالثواني
        """
        super().__init__(delay)
        self.facebook_scraper = FacebookScraper(delay)
        self.instagram_scraper = InstagramScraper(delay)
    
    def detect_platform(self, url: str) -> str:
        """
        تحديد نوع المنصة من الرابط
        
        Args:
            url: الرابط المراد تحليله
            
        Returns:
            نوع المنصة
        """
        try:
            domain = urlparse(url).netloc.lower()
            
            if 'facebook.com' in domain or 'fb.com' in domain:
                return 'facebook'
            elif 'instagram.com' in domain or 'instagr.am' in domain:
                return 'instagram'
            elif 'twitter.com' in domain or 'x.com' in domain:
                return 'twitter'
            elif 'youtube.com' in domain or 'youtu.be' in domain:
                return 'youtube'
            elif 'linkedin.com' in domain:
                return 'linkedin'
            elif 'tiktok.com' in domain:
                return 'tiktok'
            else:
                return 'generic'
                
        except:
            return 'unknown'
    
    def scrape_url(self, url: str, max_posts: int = 10) -> Dict:
        """
        استخراج المحتوى من أي رابط حسب نوع المنصة
        
        Args:
            url: الرابط المراد استخراج المحتوى منه
            max_posts: عدد المنشورات المطلوب استخراجها
            
        Returns:
            المحتوى المستخرج
        """
        platform = self.detect_platform(url)
        
        try:
            if platform == 'facebook':
                return self.facebook_scraper.scrape_facebook_page(url, max_posts)
            elif platform == 'instagram':
                return self.instagram_scraper.scrape_instagram_profile(url)
            elif platform == 'twitter':
                return self.scrape_twitter_profile(url, max_posts)
            elif platform == 'youtube':
                return self.scrape_youtube_channel(url, max_posts)
            elif platform == 'generic':
                return self.scrape_generic_website(url)
            else:
                return {'error': f'المنصة غير مدعومة: {platform}'}
                
        except Exception as e:
            return {'error': f'خطأ في استخراج المحتوى: {str(e)}'}
    
    def scrape_twitter_profile(self, url: str, max_posts: int = 10) -> Dict:
        """
        استخراج المحتوى من تويتر (محدود بسبب قيود API)
        
        Args:
            url: رابط حساب تويتر
            max_posts: عدد المنشورات
            
        Returns:
            المحتوى المستخرج
        """
        try:
            # استخراج اسم المستخدم
            username = self.extract_twitter_username(url)
            if not username:
                return {'error': 'لا يمكن استخراج اسم المستخدم من الرابط'}
            
            # محاولة استخراج المحتوى من الصفحة العامة
            soup = self.get_page(url)
            if not soup:
                return {'error': 'لا يمكن الوصول للصفحة'}
            
            # استخراج المعلومات الأساسية
            profile_info = self.extract_twitter_profile_info(soup)
            
            result = {
                'platform': 'Twitter',
                'username': username,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'profile_info': profile_info,
                'posts': [],  # تويتر يتطلب API خاص للمنشورات
                'note': 'استخراج المنشورات من تويتر يتطلب API خاص'
            }
            
            return result
            
        except Exception as e:
            return {'error': f'خطأ في استخراج محتوى تويتر: {str(e)}'}
    
    def extract_twitter_username(self, url: str) -> Optional[str]:
        """استخراج اسم المستخدم من رابط تويتر"""
        try:
            patterns = [
                r'twitter\.com/([^/?]+)',
                r'x\.com/([^/?]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    username = match.group(1)
                    username = username.split('?')[0]
                    return username
            
            return None
        except:
            return None
    
    def extract_twitter_profile_info(self, soup) -> Dict:
        """استخراج معلومات الحساب من صفحة تويتر"""
        try:
            info = {}
            
            # البحث عن البيانات في JSON-LD
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Person':
                        info['name'] = data.get('name', '')
                        info['description'] = data.get('description', '')
                        break
                except:
                    continue
            
            # استخراج العنوان
            title = soup.find('title')
            if title:
                info['title'] = self.extract_text(title)
            
            return info
            
        except Exception as e:
            print(f"خطأ في استخراج معلومات تويتر: {e}")
            return {}
    
    def scrape_youtube_channel(self, url: str, max_videos: int = 10) -> Dict:
        """
        استخراج المحتوى من قناة يوتيوب
        
        Args:
            url: رابط قناة يوتيوب
            max_videos: عدد الفيديوهات
            
        Returns:
            المحتوى المستخرج
        """
        try:
            soup = self.get_page(url)
            if not soup:
                return {'error': 'لا يمكن الوصول للصفحة'}
            
            # استخراج معلومات القناة
            channel_info = self.extract_youtube_channel_info(soup)
            
            result = {
                'platform': 'YouTube',
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'channel_info': channel_info,
                'videos': [],  # يوتيوب يتطلب API خاص للفيديوهات
                'note': 'استخراج الفيديوهات من يوتيوب يتطلب API خاص'
            }
            
            return result
            
        except Exception as e:
            return {'error': f'خطأ في استخراج محتوى يوتيوب: {str(e)}'}
    
    def extract_youtube_channel_info(self, soup) -> Dict:
        """استخراج معلومات القناة من صفحة يوتيوب"""
        try:
            info = {}
            
            # استخراج العنوان
            title = soup.find('title')
            if title:
                info['title'] = self.extract_text(title)
            
            # استخراج الوصف
            description = soup.find('meta', attrs={'name': 'description'})
            if description:
                info['description'] = description.get('content', '')
            
            return info
            
        except Exception as e:
            print(f"خطأ في استخراج معلومات يوتيوب: {e}")
            return {}
    
    def scrape_generic_website(self, url: str) -> Dict:
        """
        استخراج المحتوى من موقع ويب عام
        
        Args:
            url: رابط الموقع
            
        Returns:
            المحتوى المستخرج
        """
        try:
            result = self.scrape_generic_page(url)
            
            if not result:
                return {'error': 'لا يمكن استخراج المحتوى من الصفحة'}
            
            # تحويل المحتوى إلى تنسيق مشابه للمنصات الاجتماعية
            posts = []
            
            # إنشاء "منشور" من محتوى الصفحة
            if result.get('content', {}).get('text'):
                post = {
                    'id': f"page_{hash(url)}",
                    'text': result['content']['text'],
                    'time': result['scraped_at'],
                    'url': url,
                    'title': result.get('meta_data', {}).get('title', ''),
                    'description': result.get('meta_data', {}).get('description', ''),
                    'images': result.get('images', [])[:5]  # أول 5 صور فقط
                }
                
                # إضافة ملخص
                if post['text']:
                    post['summary'] = self.create_summary(post['text'])
                
                posts.append(post)
            
            formatted_result = {
                'platform': 'Website',
                'url': url,
                'domain': result.get('domain', ''),
                'scraped_at': result['scraped_at'],
                'site_info': result.get('meta_data', {}),
                'posts': posts,
                'total_posts': len(posts)
            }
            
            return formatted_result
            
        except Exception as e:
            return {'error': f'خطأ في استخراج محتوى الموقع: {str(e)}'}
    
    def create_summary(self, text: str, max_length: int = 200) -> str:
        """إنشاء ملخص قصير للنص"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # قطع النص عند أول نقطة بعد الحد الأدنى
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
    
    def get_supported_platforms(self) -> List[str]:
        """الحصول على قائمة المنصات المدعومة"""
        return [
            'facebook',
            'instagram', 
            'twitter',
            'youtube',
            'linkedin',
            'tiktok',
            'generic_website'
        ]

