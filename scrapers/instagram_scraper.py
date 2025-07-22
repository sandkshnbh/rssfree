"""
وحدة استخراج المحتوى من إنستغرام
"""

import json
import httpx
import jmespath
from .base_scraper import BaseScraper
from datetime import datetime
from typing import Dict, List, Optional
import re
from urllib.parse import urlparse


class InstagramScraper(BaseScraper):
    """فئة استخراج المحتوى من إنستغرام"""
    
    def __init__(self, delay: float = 2.0):
        """
        تهيئة فئة إنستغرام
        
        Args:
            delay: التأخير بين الطلبات بالثواني
        """
        super().__init__(delay)
        self.platform = "Instagram"
        
        # إعداد عميل httpx مع headers خاصة بإنستغرام
        self.client = httpx.Client(
            headers={
                "x-ig-app-id": "936619743392459",  # معرف تطبيق إنستغرام الداخلي
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "*/*",
            }
        )
    
    def extract_username_from_url(self, url: str) -> Optional[str]:
        """
        استخراج اسم المستخدم من رابط إنستغرام
        
        Args:
            url: رابط حساب إنستغرام
            
        Returns:
            اسم المستخدم أو None
        """
        try:
            # أنماط مختلفة لروابط إنستغرام
            patterns = [
                r'instagram\.com/([^/?]+)',
                r'instagr\.am/([^/?]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    username = match.group(1)
                    # تنظيف اسم المستخدم
                    username = username.split('?')[0]  # إزالة المعاملات
                    username = username.rstrip('/')
                    
                    # تجاهل الصفحات الخاصة
                    if username in ['p', 'reel', 'tv', 'stories', 'explore']:
                        return None
                    
                    return username
            
            return None
            
        except Exception as e:
            print(f"خطأ في استخراج اسم المستخدم: {e}")
            return None
    
    def scrape_instagram_profile(self, url: str) -> Dict:
        """
        استخراج المحتوى من حساب إنستغرام
        
        Args:
            url: رابط حساب إنستغرام
            
        Returns:
            قاموس يحتوي على معلومات الحساب والمنشورات
        """
        username = self.extract_username_from_url(url)
        if not username:
            return {'error': 'لا يمكن استخراج اسم المستخدم من الرابط'}
        
        try:
            # استخراج بيانات الحساب
            result = self.client.get(
                f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}",
            )
            
            if result.status_code != 200:
                return {'error': f'فشل في الوصول للحساب: {result.status_code}'}
            
            data = json.loads(result.content)
            user_data = data.get("data", {}).get("user", {})
            
            if not user_data:
                return {'error': 'لم يتم العثور على بيانات المستخدم'}
            
            # معالجة البيانات
            processed_data = self.parse_instagram_profile(user_data)
            processed_data.update({
                'platform': self.platform,
                'username': username,
                'url': url,
                'scraped_at': datetime.now().isoformat()
            })
            
            return processed_data
            
        except Exception as e:
            return {'error': f'خطأ في استخراج المحتوى: {str(e)}'}
    
    def parse_instagram_profile(self, data: Dict) -> Dict:
        """
        معالجة بيانات حساب إنستغرام باستخدام JMESPath
        
        Args:
            data: البيانات الخام للحساب
            
        Returns:
            البيانات المعالجة
        """
        try:
            result = jmespath.search(
                """{
                name: full_name,
                username: username,
                id: id,
                bio: biography,
                bio_links: bio_links[].url,
                homepage: external_url,
                followers: edge_followed_by.count,
                follows: edge_follow.count,
                is_private: is_private,
                is_verified: is_verified,
                profile_image: profile_pic_url_hd,
                post_count: edge_owner_to_timeline_media.count,
                posts: edge_owner_to_timeline_media.edges[].node.{
                    id: id,
                    shortcode: shortcode,
                    display_url: display_url,
                    is_video: is_video,
                    caption: edge_media_to_caption.edges[0].node.text,
                    comments_count: edge_media_to_comment.count,
                    likes_count: edge_liked_by.count,
                    taken_at: taken_at_timestamp,
                    location: location.name
                }
                }""", data
            )
            
            # معالجة المنشورات
            if result and result.get('posts'):
                processed_posts = []
                for post in result['posts']:
                    processed_post = self.process_instagram_post(post)
                    if processed_post:
                        processed_posts.append(processed_post)
                
                result['posts'] = processed_posts
                result['total_posts'] = len(processed_posts)
            
            return result or {}
            
        except Exception as e:
            print(f"خطأ في معالجة البيانات: {e}")
            return {}
    
    def process_instagram_post(self, post: Dict) -> Optional[Dict]:
        """
        معالجة منشور إنستغرام
        
        Args:
            post: بيانات المنشور الخام
            
        Returns:
            منشور معالج أو None
        """
        try:
            processed = {
                'id': post.get('id', ''),
                'shortcode': post.get('shortcode', ''),
                'caption': post.get('caption', ''),
                'display_url': post.get('display_url', ''),
                'is_video': post.get('is_video', False),
                'comments_count': post.get('comments_count', 0),
                'likes_count': post.get('likes_count', 0),
                'taken_at': self.format_timestamp(post.get('taken_at')),
                'location': post.get('location', ''),
                'post_url': f"https://www.instagram.com/p/{post.get('shortcode', '')}/" if post.get('shortcode') else ''
            }
            
            # تنظيف النص
            if processed['caption']:
                processed['caption'] = self.clean_instagram_caption(processed['caption'])
                processed['summary'] = self.create_summary(processed['caption'])
            
            return processed
            
        except Exception as e:
            print(f"خطأ في معالجة المنشور: {e}")
            return None
    
    def clean_instagram_caption(self, caption: str) -> str:
        """تنظيف نص المنشور من الهاشتاغات والإشارات"""
        if not caption:
            return ""
        
        # إزالة الهاشتاغات الزائدة (الاحتفاظ بالأولى فقط)
        hashtags = re.findall(r'#\w+', caption)
        if len(hashtags) > 5:
            # الاحتفاظ بأول 5 هاشتاغات فقط
            for hashtag in hashtags[5:]:
                caption = caption.replace(hashtag, '', 1)
        
        # تنظيف المسافات الزائدة
        caption = re.sub(r'\s+', ' ', caption)
        
        return caption.strip()
    
    def create_summary(self, text: str, max_length: int = 150) -> str:
        """إنشاء ملخص قصير للنص"""
        if not text:
            return ""
        
        # إزالة الهاشتاغات من الملخص
        text_without_hashtags = re.sub(r'#\w+', '', text)
        text_without_hashtags = re.sub(r'\s+', ' ', text_without_hashtags).strip()
        
        if len(text_without_hashtags) <= max_length:
            return text_without_hashtags
        
        # قطع النص عند أول نقطة أو فاصلة
        min_length = max_length // 2
        
        for i in range(min_length, min(len(text_without_hashtags), max_length)):
            if text_without_hashtags[i] in '.!?':
                return text_without_hashtags[:i+1].strip()
        
        # إذا لم نجد نقطة، نقطع عند آخر مسافة
        truncated = text_without_hashtags[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > min_length:
            return truncated[:last_space] + "..."
        
        return truncated + "..."
    
    def format_timestamp(self, timestamp) -> str:
        """تحويل timestamp إلى تاريخ مقروء"""
        if not timestamp:
            return ""
        
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.isoformat()
        except:
            return str(timestamp)
    
    def is_instagram_url(self, url: str) -> bool:
        """التحقق من أن الرابط ينتمي لإنستغرام"""
        try:
            domain = urlparse(url).netloc.lower()
            return 'instagram.com' in domain or 'instagr.am' in domain
        except:
            return False
    
    def get_profile_info_only(self, url: str) -> Dict:
        """
        الحصول على معلومات الحساب فقط دون المنشورات
        
        Args:
            url: رابط حساب إنستغرام
            
        Returns:
            معلومات الحساب
        """
        full_data = self.scrape_instagram_profile(url)
        
        if 'error' in full_data:
            return full_data
        
        # إزالة المنشورات والاحتفاظ بالمعلومات الأساسية فقط
        profile_info = {k: v for k, v in full_data.items() if k != 'posts'}
        
        return profile_info

