# 💼 Pro Data Analyzer

![Tests Passing](https://github.com/222kadimm-ux/data-analyzer/actions/workflows/tests.yml/badge.svg)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://data-analyzer-vzl8jspasawmzxey7gezcm.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Analyseur de Données Industrielles (OEE & IA)** | محلل بيانات المصانع

منصة تحليل بيانات ذكية مدعومة بالذكاء الاصطناعي. تتيح لك رفع ملفات Excel/CSV أو الاتصال المباشر بـ Google Sheets أو قواعد بيانات SQL، لتحليلها فوراً وحساب مؤشرات التصنيع (OEE)، والتنبؤ بالمستقبل، والحصول على تقارير بالذكاء الاصطناعي.

## ✨ الميزات الرئيسية (Features)
- 🏭 **حساب OEE:** حساب الإتاحة، الأداء، الجودة، والفعالية الكلية للمعدات.
- 🔮 **التنبؤ بالمستقبل (Forecasting):** توقع المبيعات أو الإنتاج باستخدام Prophet.
- 🤖 **المحادثة مع البيانات (AI Chat):** اسأل بياناتك بالعربية أو الفرنسية.
- 🗣️ **AI to SQL:** تحويل الأسئلة الطبيعية إلى استعلامات SQL وتنفيذها على قواعد بيانات المصانع.
- 🔗 **التكاملات (Integrations):** رفع ملفات، Google Sheets، وقواعد بيانات SQL (PostgreSQL).
- 📊 **لوحة تحكم إحصائية:** مصفوفة الارتباطات (Correlation Matrix) وتحليل باريتو.
- 🌐 **دعم لغتين (i18n):** الفرنسية (افتراضياً) والعربية.
- 🔒 **حفظ تلقائي:** باستخدام UUID + Cookie (بدون الحاجة لتسجيل دخول).

## 🏗️ هندسة المشروع (Architecture)
- **الواجهة (Frontend):** Streamlit (Python)
- **قاعدة البيانات (Database):** Neon (PostgreSQL) + SQLAlchemy
- **محرك التحليل (Data Engine):** Polars (للملفات الكبيرة)
- **الذكاء الاصطناعي (AI):** OpenRouter (Llama 3)
- **المراقبة (Monitoring):** Sentry

## 🚀 جرّب التطبيق الآن (Live Demo)
[اضغط هنا لفتح التطبيق المباشر](https://data-analyzer-vzl8jspasawmzxey7gezcm.streamlit.app)

## 🛠️ التشغيل المحلي (Local Setup)
1. استنسخ المستودع:
   ```bash
   git clone https://github.com/222kadimm-ux/data-analyzer.git
