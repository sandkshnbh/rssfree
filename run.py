#!/usr/bin/env python3
"""
ملف تشغيل أداة RSS للتواصل الاجتماعي
"""

import os
import sys
from app import app, logger

def main():
    """تشغيل التطبيق"""
    try:
        # التحقق من المتطلبات
        check_requirements()
        
        # إعداد المتغيرات
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info("=" * 50)
        logger.info("🚀 بدء تشغيل أداة RSS للتواصل الاجتماعي")
        logger.info("=" * 50)
        logger.info(f"📡 الخادم: http://{host}:{port}")
        logger.info(f"🔧 وضع التطوير: {'مُفعل' if debug else 'مُعطل'}")
        logger.info(f"📁 مجلد الخلاصات: {os.path.join(os.path.dirname(__file__), 'feeds')}")
        logger.info("=" * 50)
        
        # تشغيل التطبيق
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  تم إيقاف التطبيق بواسطة المستخدم")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل التطبيق: {str(e)}")
        sys.exit(1)

def check_requirements():
    """التحقق من المتطلبات الأساسية"""
    required_modules = [
        'flask',
        'flask_cors',
        'requests',
        'beautifulsoup4',
        'feedgen',
        'facebook_scraper',
        'httpx',
        'jmespath'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error("❌ المكتبات التالية مفقودة:")
        for module in missing_modules:
            logger.error(f"   - {module}")
        logger.error("\n💡 لتثبيت المكتبات المفقودة، استخدم:")
        logger.error("   pip install -r requirements.txt")
        sys.exit(1)
    
    logger.info("✅ جميع المتطلبات متوفرة")

if __name__ == '__main__':
    main()

