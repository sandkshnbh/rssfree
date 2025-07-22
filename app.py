"""
تطبيق Flask الرئيسي لأداة RSS للتواصل الاجتماعي
"""

from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS
import os
import sys
from datetime import datetime
import logging

# إضافة المجلد الحالي إلى مسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد الوحدات المخصصة
from scrapers.multi_platform_scraper import MultiPlatformScraper
from rss_generator.feed_manager import FeedManager

# إعداد التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'rss-social-tool-secret-key-2025'

# تمكين CORS للسماح بالطلبات من أي مصدر
CORS(app)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء مجلد الخلاصات
FEEDS_DIR = os.path.join(os.path.dirname(__file__), 'feeds')
os.makedirs(FEEDS_DIR, exist_ok=True)

# تهيئة المكونات
scraper = MultiPlatformScraper()
feed_manager = FeedManager(FEEDS_DIR)


@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')


@app.route('/api/create-feed', methods=['POST'])
def create_feed():
    """إنشاء خلاصة RSS جديدة"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'يرجى تقديم رابط صحيح'}), 400
        
        url = data['url'].strip()
        max_posts = data.get('max_posts', 10)
        
        if not url:
            return jsonify({'error': 'يرجى تقديم رابط صحيح'}), 400
        
        logger.info(f"Creating RSS feed for URL: {url}")
        
        # استخراج المحتوى من الرابط
        scraped_data = scraper.scrape_url(url, max_posts)
        
        if 'error' in scraped_data:
            logger.error(f"Scraping error: {scraped_data['error']}")
            return jsonify({'error': scraped_data['error']}), 400
        
        # إنشاء خلاصة RSS
        feed_info = feed_manager.create_feed(url, scraped_data)
        
        if 'error' in feed_info:
            logger.error(f"Feed creation error: {feed_info['error']}")
            return jsonify({'error': feed_info['error']}), 500
        
        logger.info(f"RSS feed created successfully: {feed_info['id']}")
        return jsonify(feed_info)
        
    except Exception as e:
        logger.error(f"Unexpected error in create_feed: {str(e)}")
        return jsonify({'error': 'حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.'}), 500


@app.route('/api/feeds', methods=['GET'])
def get_feeds():
    """الحصول على جميع الخلاصات"""
    try:
        feeds = feed_manager.get_all_feeds()
        return jsonify(feeds)
    except Exception as e:
        logger.error(f"Error getting feeds: {str(e)}")
        return jsonify({'error': 'فشل في جلب الخلاصات'}), 500


@app.route('/api/feeds/<feed_id>', methods=['GET'])
def get_feed(feed_id):
    """الحصول على خلاصة محددة"""
    try:
        feed_info = feed_manager.get_feed_info(feed_id)
        
        if not feed_info:
            return jsonify({'error': 'الخلاصة غير موجودة'}), 404
        
        return jsonify(feed_info)
    except Exception as e:
        logger.error(f"Error getting feed {feed_id}: {str(e)}")
        return jsonify({'error': 'فشل في جلب الخلاصة'}), 500


@app.route('/api/feeds/<feed_id>', methods=['DELETE'])
def delete_feed(feed_id):
    """حذف خلاصة"""
    try:
        success = feed_manager.delete_feed(feed_id)
        
        if success:
            logger.info(f"Feed deleted successfully: {feed_id}")
            return jsonify({'message': 'تم حذف الخلاصة بنجاح'})
        else:
            return jsonify({'error': 'الخلاصة غير موجودة'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting feed {feed_id}: {str(e)}")
        return jsonify({'error': 'فشل في حذف الخلاصة'}), 500


@app.route('/api/feeds/<feed_id>/update', methods=['POST'])
def update_feed(feed_id):
    """تحديث خلاصة موجودة"""
    try:
        feed_info = feed_manager.get_feed_info(feed_id)
        
        if not feed_info:
            return jsonify({'error': 'الخلاصة غير موجودة'}), 404
        
        url = feed_info['url']
        logger.info(f"Updating RSS feed: {feed_id}")
        
        # استخراج المحتوى المحدث
        scraped_data = scraper.scrape_url(url, 10)
        
        if 'error' in scraped_data:
            logger.error(f"Scraping error during update: {scraped_data['error']}")
            return jsonify({'error': scraped_data['error']}), 400
        
        # تحديث الخلاصة
        updated_feed = feed_manager.update_feed(feed_id, scraped_data)
        
        if 'error' in updated_feed:
            logger.error(f"Feed update error: {updated_feed['error']}")
            return jsonify({'error': updated_feed['error']}), 500
        
        logger.info(f"RSS feed updated successfully: {feed_id}")
        return jsonify(updated_feed)
        
    except Exception as e:
        logger.error(f"Unexpected error updating feed {feed_id}: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء تحديث الخلاصة'}), 500


@app.route('/feeds/<feed_id>.xml')
def serve_rss_feed(feed_id):
    """تقديم ملف RSS XML"""
    try:
        feed_info = feed_manager.get_feed_info(feed_id)
        
        if not feed_info:
            abort(404)
        
        xml_path = feed_info['xml_path']
        
        if not os.path.exists(xml_path):
            abort(404)
        
        return send_file(
            xml_path,
            mimetype='application/rss+xml',
            as_attachment=False,
            download_name=f'feed_{feed_id}.xml'
        )
        
    except Exception as e:
        logger.error(f"Error serving RSS feed {feed_id}: {str(e)}")
        abort(500)


@app.route('/api/stats')
def get_stats():
    """الحصول على إحصائيات الخلاصات"""
    try:
        stats = feed_manager.get_feed_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'فشل في جلب الإحصائيات'}), 500


@app.route('/api/search')
def search_feeds():
    """البحث في الخلاصات"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'يرجى تقديم كلمة بحث'}), 400
        
        results = feed_manager.search_feeds(query)
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error searching feeds: {str(e)}")
        return jsonify({'error': 'فشل في البحث'}), 500


@app.route('/api/platforms')
def get_supported_platforms():
    """الحصول على المنصات المدعومة"""
    try:
        platforms = scraper.get_supported_platforms()
        return jsonify({
            'platforms': platforms,
            'count': len(platforms)
        })
    except Exception as e:
        logger.error(f"Error getting platforms: {str(e)}")
        return jsonify({'error': 'فشل في جلب المنصات المدعومة'}), 500


@app.route('/api/health')
def health_check():
    """فحص صحة التطبيق"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.errorhandler(404)
def not_found(error):
    """معالج خطأ 404"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'المورد غير موجود'}), 404
    return render_template('index.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """معالج خطأ 500"""
    logger.error(f"Internal server error: {str(error)}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'خطأ داخلي في الخادم'}), 500
    return render_template('index.html'), 500


@app.before_request
def log_request():
    """تسجيل الطلبات"""
    if not request.path.startswith('/static/'):
        logger.info(f"{request.method} {request.path} - {request.remote_addr}")


@app.after_request
def after_request(response):
    """إضافة headers للاستجابة"""
    # إضافة headers للأمان
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # إضافة headers للـ RSS
    if request.path.endswith('.xml'):
        response.headers['Cache-Control'] = 'public, max-age=3600'  # تخزين مؤقت لساعة واحدة
    
    return response


def cleanup_old_feeds():
    """تنظيف الخلاصات القديمة"""
    try:
        deleted_count = feed_manager.cleanup_old_feeds(max_age_days=30)
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old feeds")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")


if __name__ == '__main__':
    # تنظيف الخلاصات القديمة عند بدء التطبيق
    cleanup_old_feeds()
    
    # تشغيل التطبيق
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting RSS Social Tool on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Feeds directory: {FEEDS_DIR}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )

