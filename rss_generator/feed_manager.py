"""
مدير خلاصات RSS - لإدارة وحفظ الخلاصات
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .rss_generator import RSSGenerator


class FeedManager:
    """فئة إدارة خلاصات RSS"""
    
    def __init__(self, feeds_dir: str = "feeds"):
        """
        تهيئة مدير الخلاصات
        
        Args:
            feeds_dir: مجلد حفظ الخلاصات
        """
        self.feeds_dir = feeds_dir
        self.metadata_file = os.path.join(feeds_dir, "feeds_metadata.json")
        
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(feeds_dir, exist_ok=True)
        
        # تحميل البيانات الوصفية
        self.metadata = self.load_metadata()
    
    def load_metadata(self) -> Dict:
        """تحميل البيانات الوصفية للخلاصات"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"خطأ في تحميل البيانات الوصفية: {e}")
        
        return {}
    
    def save_metadata(self):
        """حفظ البيانات الوصفية"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطأ في حفظ البيانات الوصفية: {e}")
    
    def generate_feed_id(self, url: str) -> str:
        """إنشاء معرف فريد للخلاصة"""
        return str(abs(hash(url)))[:10]
    
    def create_feed(self, url: str, scraped_data: Dict, update_interval: int = 60) -> Dict:
        """
        إنشاء خلاصة RSS جديدة
        
        Args:
            url: رابط المصدر
            scraped_data: البيانات المستخرجة
            update_interval: فترة التحديث بالدقائق
            
        Returns:
            معلومات الخلاصة المُنشأة
        """
        try:
            # إنشاء معرف الخلاصة
            feed_id = self.generate_feed_id(url)
            
            # إنشاء مولد RSS
            rss_generator = RSSGenerator()
            rss_xml = rss_generator.create_feed_from_scraped_data(scraped_data)
            
            if not rss_xml:
                return {'error': 'فشل في إنشاء خلاصة RSS'}
            
            # حفظ ملف XML
            xml_filename = f"{feed_id}.xml"
            xml_path = os.path.join(self.feeds_dir, xml_filename)
            
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(rss_xml)
            
            # إعداد معلومات الخلاصة
            feed_info = {
                'id': feed_id,
                'url': url,
                'platform': scraped_data.get('platform', 'Unknown'),
                'title': f"خلاصة {scraped_data.get('username', scraped_data.get('page_name', 'مستخدم'))} على {scraped_data.get('platform', 'منصة التواصل الاجتماعي')}",
                'description': f"آخر المنشورات من {scraped_data.get('username', scraped_data.get('page_name', 'مستخدم'))}",
                'xml_file': xml_filename,
                'xml_path': xml_path,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'update_interval': update_interval,
                'post_count': len(scraped_data.get('posts', [])),
                'rss_url': f"/feeds/{xml_filename}",
                'status': 'active'
            }
            
            # حفظ في البيانات الوصفية
            self.metadata[feed_id] = feed_info
            self.save_metadata()
            
            return feed_info
            
        except Exception as e:
            return {'error': f'خطأ في إنشاء الخلاصة: {str(e)}'}
    
    def update_feed(self, feed_id: str, scraped_data: Dict) -> Dict:
        """
        تحديث خلاصة موجودة
        
        Args:
            feed_id: معرف الخلاصة
            scraped_data: البيانات الجديدة
            
        Returns:
            معلومات الخلاصة المحدثة
        """
        try:
            if feed_id not in self.metadata:
                return {'error': 'الخلاصة غير موجودة'}
            
            feed_info = self.metadata[feed_id]
            
            # إنشاء مولد RSS
            rss_generator = RSSGenerator()
            rss_xml = rss_generator.create_feed_from_scraped_data(scraped_data)
            
            if not rss_xml:
                return {'error': 'فشل في تحديث خلاصة RSS'}
            
            # حفظ ملف XML المحدث
            xml_path = feed_info['xml_path']
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(rss_xml)
            
            # تحديث معلومات الخلاصة
            feed_info['last_updated'] = datetime.now().isoformat()
            feed_info['post_count'] = len(scraped_data.get('posts', []))
            
            self.save_metadata()
            
            return feed_info
            
        except Exception as e:
            return {'error': f'خطأ في تحديث الخلاصة: {str(e)}'}
    
    def get_feed_info(self, feed_id: str) -> Optional[Dict]:
        """الحصول على معلومات خلاصة"""
        return self.metadata.get(feed_id)
    
    def get_all_feeds(self) -> List[Dict]:
        """الحصول على جميع الخلاصات"""
        return list(self.metadata.values())
    
    def delete_feed(self, feed_id: str) -> bool:
        """
        حذف خلاصة
        
        Args:
            feed_id: معرف الخلاصة
            
        Returns:
            True إذا تم الحذف بنجاح
        """
        try:
            if feed_id not in self.metadata:
                return False
            
            feed_info = self.metadata[feed_id]
            
            # حذف ملف XML
            xml_path = feed_info.get('xml_path')
            if xml_path and os.path.exists(xml_path):
                os.remove(xml_path)
            
            # حذف من البيانات الوصفية
            del self.metadata[feed_id]
            self.save_metadata()
            
            return True
            
        except Exception as e:
            print(f"خطأ في حذف الخلاصة: {e}")
            return False
    
    def get_feeds_needing_update(self) -> List[Dict]:
        """الحصول على الخلاصات التي تحتاج تحديث"""
        feeds_to_update = []
        current_time = datetime.now()
        
        for feed_info in self.metadata.values():
            if feed_info.get('status') != 'active':
                continue
            
            last_updated = datetime.fromisoformat(feed_info['last_updated'])
            update_interval = feed_info.get('update_interval', 60)
            
            if current_time - last_updated > timedelta(minutes=update_interval):
                feeds_to_update.append(feed_info)
        
        return feeds_to_update
    
    def cleanup_old_feeds(self, max_age_days: int = 30):
        """تنظيف الخلاصات القديمة"""
        current_time = datetime.now()
        feeds_to_delete = []
        
        for feed_id, feed_info in self.metadata.items():
            last_updated = datetime.fromisoformat(feed_info['last_updated'])
            
            if current_time - last_updated > timedelta(days=max_age_days):
                feeds_to_delete.append(feed_id)
        
        for feed_id in feeds_to_delete:
            self.delete_feed(feed_id)
        
        return len(feeds_to_delete)
    
    def get_feed_stats(self) -> Dict:
        """الحصول على إحصائيات الخلاصات"""
        total_feeds = len(self.metadata)
        active_feeds = len([f for f in self.metadata.values() if f.get('status') == 'active'])
        
        platforms = {}
        for feed_info in self.metadata.values():
            platform = feed_info.get('platform', 'Unknown')
            platforms[platform] = platforms.get(platform, 0) + 1
        
        return {
            'total_feeds': total_feeds,
            'active_feeds': active_feeds,
            'platforms': platforms,
            'feeds_dir': self.feeds_dir
        }
    
    def search_feeds(self, query: str) -> List[Dict]:
        """البحث في الخلاصات"""
        results = []
        query_lower = query.lower()
        
        for feed_info in self.metadata.values():
            if (query_lower in feed_info.get('title', '').lower() or
                query_lower in feed_info.get('description', '').lower() or
                query_lower in feed_info.get('platform', '').lower()):
                results.append(feed_info)
        
        return results

