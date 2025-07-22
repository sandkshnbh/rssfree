"""
مولد خلاصات RSS من محتوى وسائل التواصل الاجتماعي
"""

from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from typing import Dict, List, Optional
import re
from urllib.parse import urljoin
import uuid


class RSSGenerator:
    """فئة مولد خلاصات RSS"""
    
    def __init__(self):
        """تهيئة مولد RSS"""
        self.fg = None
        self.base_url = "https://rss-social-tool.com"  # يمكن تغييره حسب النطاق الفعلي
    
    def create_feed(self, 
                   title: str,
                   description: str,
                   link: str,
                   language: str = "ar",
                   author_name: str = "RSS Social Tool",
                   author_email: str = "info@rss-social-tool.com") -> FeedGenerator:
        """
        إنشاء خلاصة RSS جديدة
        
        Args:
            title: عنوان الخلاصة
            description: وصف الخلاصة
            link: رابط الخلاصة
            language: لغة المحتوى
            author_name: اسم المؤلف
            author_email: بريد المؤلف الإلكتروني
            
        Returns:
            كائن FeedGenerator
        """
        self.fg = FeedGenerator()
        
        # إعداد معلومات الخلاصة الأساسية
        self.fg.title(title)
        self.fg.description(description)
        self.fg.link(href=link, rel='alternate')
        self.fg.link(href=f"{self.base_url}/rss/{self.generate_feed_id(link)}.xml", rel='self')
        self.fg.language(language)
        
        # إعداد معلومات المؤلف
        self.fg.author(name=author_name, email=author_email)
        
        # إعداد معلومات إضافية
        self.fg.generator("RSS Social Tool - أداة مجانية لإنشاء خلاصات RSS")
        self.fg.lastBuildDate(datetime.now(timezone.utc))
        self.fg.pubDate(datetime.now(timezone.utc))
        
        # إعداد معلومات الصورة (لوجو الخلاصة)
        self.fg.image(
            url=f"{self.base_url}/static/images/rss-logo.png",
            title=title,
            link=link,
            description=f"لوجو خلاصة {title}"
        )
        
        # إعداد معلومات إضافية للـ RSS
        self.fg.managingEditor(author_email)
        self.fg.webMaster(author_email)
        self.fg.category(term="Social Media", label="وسائل التواصل الاجتماعي")
        self.fg.ttl(60)  # تحديث كل ساعة
        
        return self.fg
    
    def add_post_to_feed(self, post_data: Dict) -> bool:
        """
        إضافة منشور إلى الخلاصة
        
        Args:
            post_data: بيانات المنشور
            
        Returns:
            True إذا تمت الإضافة بنجاح
        """
        if not self.fg:
            return False
        
        try:
            fe = self.fg.add_entry()
            
            # إعداد معلومات المنشور الأساسية
            title = self.generate_post_title(post_data)
            fe.title(title)
            
            # إعداد الرابط
            post_url = post_data.get('post_url', post_data.get('url', ''))
            if post_url:
                fe.link(href=post_url)
                fe.guid(post_url, permalink=True)
            else:
                # إنشاء GUID فريد إذا لم يكن هناك رابط
                fe.guid(str(uuid.uuid4()), permalink=False)
            
            # إعداد المحتوى
            content = self.generate_post_content(post_data)
            fe.description(content)
            
            # إضافة المحتوى الكامل إذا كان متوفراً
            full_content = self.generate_full_content(post_data)
            if full_content:
                fe.content(content=full_content, type='html')
            
            # إعداد التاريخ
            post_time = self.parse_post_time(post_data.get('time', post_data.get('taken_at')))
            if post_time:
                fe.pubDate(post_time)
            else:
                fe.pubDate(datetime.now(timezone.utc))
            
            # إعداد المؤلف
            author = post_data.get('username', post_data.get('author', 'مجهول'))
            fe.author(name=author)
            
            # إضافة الفئات (الهاشتاغات)
            self.add_categories_to_entry(fe, post_data)
            
            # إضافة الصور كمرفقات
            self.add_enclosures_to_entry(fe, post_data)
            
            return True
            
        except Exception as e:
            print(f"خطأ في إضافة المنشور للخلاصة: {e}")
            return False
    
    def generate_post_title(self, post_data: Dict) -> str:
        """إنشاء عنوان للمنشور"""
        # محاولة استخدام العنوان إذا كان متوفراً
        if post_data.get('title'):
            return post_data['title']
        
        # استخدام الملخص إذا كان متوفراً
        if post_data.get('summary'):
            return post_data['summary'][:100] + "..." if len(post_data['summary']) > 100 else post_data['summary']
        
        # استخدام بداية النص
        text = post_data.get('text', post_data.get('caption', ''))
        if text:
            # تنظيف النص من الهاشتاغات والروابط
            clean_text = re.sub(r'#\w+|http[s]?://\S+', '', text)
            clean_text = clean_text.strip()
            
            if clean_text:
                return clean_text[:100] + "..." if len(clean_text) > 100 else clean_text
        
        # عنوان افتراضي
        platform = post_data.get('platform', 'منصة التواصل الاجتماعي')
        username = post_data.get('username', 'مستخدم')
        return f"منشور جديد من {username} على {platform}"
    
    def generate_post_content(self, post_data: Dict) -> str:
        """إنشاء محتوى المنشور للوصف"""
        content_parts = []
        
        # إضافة النص الرئيسي
        text = post_data.get('text', post_data.get('caption', ''))
        if text:
            content_parts.append(text)
        
        # إضافة معلومات إضافية
        if post_data.get('likes_count') or post_data.get('likes'):
            likes = post_data.get('likes_count', post_data.get('likes', 0))
            content_parts.append(f"👍 {likes} إعجاب")
        
        if post_data.get('comments_count') or post_data.get('comments'):
            comments = post_data.get('comments_count', post_data.get('comments', 0))
            content_parts.append(f"💬 {comments} تعليق")
        
        if post_data.get('shares'):
            shares = post_data.get('shares', 0)
            content_parts.append(f"🔄 {shares} مشاركة")
        
        return " | ".join(content_parts) if content_parts else "محتوى غير متوفر"
    
    def generate_full_content(self, post_data: Dict) -> str:
        """إنشاء المحتوى الكامل بتنسيق HTML"""
        html_parts = []
        
        # إضافة النص الرئيسي
        text = post_data.get('text', post_data.get('caption', ''))
        if text:
            # تحويل الهاشتاغات إلى روابط
            text_with_links = re.sub(
                r'#(\w+)', 
                r'<a href="https://www.instagram.com/explore/tags/\1/">#\1</a>', 
                text
            )
            html_parts.append(f"<p>{text_with_links}</p>")
        
        # إضافة الصور
        images = post_data.get('images', [])
        if images:
            html_parts.append("<div class='images'>")
            for img_url in images[:3]:  # أول 3 صور فقط
                html_parts.append(f'<img src="{img_url}" alt="صورة المنشور" style="max-width: 100%; margin: 5px;">')
            html_parts.append("</div>")
        
        # إضافة معلومات التفاعل
        interaction_parts = []
        if post_data.get('likes_count') or post_data.get('likes'):
            likes = post_data.get('likes_count', post_data.get('likes', 0))
            interaction_parts.append(f"👍 {likes} إعجاب")
        
        if post_data.get('comments_count') or post_data.get('comments'):
            comments = post_data.get('comments_count', post_data.get('comments', 0))
            interaction_parts.append(f"💬 {comments} تعليق")
        
        if interaction_parts:
            html_parts.append(f"<p><small>{' | '.join(interaction_parts)}</small></p>")
        
        # إضافة رابط المنشور الأصلي
        post_url = post_data.get('post_url', post_data.get('url', ''))
        if post_url:
            html_parts.append(f'<p><a href="{post_url}">عرض المنشور الأصلي</a></p>')
        
        return "".join(html_parts) if html_parts else "<p>محتوى غير متوفر</p>"
    
    def add_categories_to_entry(self, entry, post_data: Dict):
        """إضافة الفئات (الهاشتاغات) للمنشور"""
        text = post_data.get('text', post_data.get('caption', ''))
        if text:
            # استخراج الهاشتاغات
            hashtags = re.findall(r'#(\w+)', text)
            for hashtag in hashtags[:5]:  # أول 5 هاشتاغات فقط
                entry.category(term=hashtag, label=f"#{hashtag}")
        
        # إضافة فئة المنصة
        platform = post_data.get('platform', '')
        if platform:
            entry.category(term=platform, label=platform)
    
    def add_enclosures_to_entry(self, entry, post_data: Dict):
        """إضافة المرفقات (الصور/الفيديوهات) للمنشور"""
        # إضافة الصور
        images = post_data.get('images', [])
        for img_url in images[:1]:  # صورة واحدة فقط كمرفق
            try:
                entry.enclosure(url=img_url, type="image/jpeg", length="0")
                break
            except:
                continue
        
        # إضافة الفيديو إذا كان متوفراً
        video_url = post_data.get('video', post_data.get('video_url', ''))
        if video_url:
            try:
                entry.enclosure(url=video_url, type="video/mp4", length="0")
            except:
                pass
    
    def parse_post_time(self, time_str) -> Optional[datetime]:
        """تحويل وقت المنشور إلى datetime"""
        if not time_str:
            return None
        
        try:
            if isinstance(time_str, datetime):
                return time_str.replace(tzinfo=timezone.utc)
            
            if isinstance(time_str, str):
                # محاولة تحليل التاريخ بصيغ مختلفة
                try:
                    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                except:
                    pass
                
                try:
                    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"خطأ في تحليل الوقت: {e}")
            return None
    
    def generate_feed_id(self, url: str) -> str:
        """إنشاء معرف فريد للخلاصة"""
        return str(hash(url))[:10].replace('-', '0')
    
    def generate_rss_xml(self) -> str:
        """إنشاء XML للخلاصة"""
        if not self.fg:
            return ""
        
        try:
            return self.fg.rss_str(pretty=True).decode('utf-8')
        except Exception as e:
            print(f"خطأ في إنشاء XML: {e}")
            return ""
    
    def save_rss_file(self, filename: str) -> bool:
        """حفظ الخلاصة في ملف"""
        if not self.fg:
            return False
        
        try:
            self.fg.rss_file(filename)
            return True
        except Exception as e:
            print(f"خطأ في حفظ الملف: {e}")
            return False
    
    def create_feed_from_scraped_data(self, scraped_data: Dict) -> str:
        """
        إنشاء خلاصة RSS من البيانات المستخرجة
        
        Args:
            scraped_data: البيانات المستخرجة من المنصة
            
        Returns:
            XML للخلاصة
        """
        try:
            # إعداد معلومات الخلاصة
            platform = scraped_data.get('platform', 'منصة التواصل الاجتماعي')
            username = scraped_data.get('username', scraped_data.get('page_name', 'مستخدم'))
            
            title = f"خلاصة {username} على {platform}"
            description = f"آخر المنشورات من {username} على {platform}"
            link = scraped_data.get('url', '')
            
            # إنشاء الخلاصة
            self.create_feed(title, description, link)
            
            # إضافة المنشورات
            posts = scraped_data.get('posts', [])
            for post in posts:
                self.add_post_to_feed(post)
            
            # إنشاء XML
            return self.generate_rss_xml()
            
        except Exception as e:
            print(f"خطأ في إنشاء الخلاصة: {e}")
            return ""

