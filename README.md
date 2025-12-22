# MEIH Movies API (Backend & Proxy)

نظام خلفي متكامل يوفر واجهة برمجة تطبيقات (API) لمنصة بث الأفلام والمسلسلات، مدمج معه خدمة بروكسي لتجاوز الحجب.

## 🚀 المميزات

- **FastAPI**: أداء عالي وسرعة استجابة.
- **Scraper Engine**: محرك قوي لجلب البيانات من المصادر.
- **Integrated Proxy**: بروكسي Node.js مدمج لتجاوز حماية Cloudflare وغيرها.
- **Keep-Alive**: نظام ذاتي لمنع السيرفر من الدخول في وضع السكون على Render.

## 🛠️ التثبيت والتشغيل محلياً

1. **تثبيت المتطلبات**:

   ```bash
   pip install -r requirements.txt
   cd proxy-service && npm install
   ```

2. **التشغيل**:
   قم بتشغيل الملف المجمع:
   ```bash
   start-all.bat
   ```

## ☁️ النشر على Render

هذا المشروع مهيأ للعمل كخدمة واحدة (Monorepo) على Render:

1. اربط المستودع بخدمة Web Service.
2. استخدم `Environment: Python`.
3. **Build Command**: `bash setup_render.sh`
4. **Start Command**: `bash start_render.sh`
5. أضف المتغيرات البيئية:
   - `NODE_PROXY_URL`: `http://localhost:3001`

---

Developed by Mina Samir using Advanced AI Agents.
