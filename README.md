# 💼 Pro Data Analyzer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://data-analyzer-vzl8jspasawmzxey7gezcm.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

منصة تحليل بيانات ذكية مدعومة بالذكاء الاصطناعي، تتيح لك رفع ملفات Excel/CSV أو الاتصال المباشر بـ Google Sheets، لتحليلها فوراً والحصول على رؤى مبنية على بياناتك باللغة العربية.

## ✨ الميزات الرئيسية
- 🤖 **محادثة مع البيانات:** اسأل بياناتك باللغة الطبيعية واحصل على إجابات إحصائية.
- 🔗 **تكامل Google Sheets:** اسحب بياناتك مباشرة من جداول جوجل.
- 📊 **رسوم بيانية تفاعلية:** تحليل بصري فوري (Bar/Pie Charts).
- 📥 **تصدير مرن:** تحميل النتائج بصيغة CSV أو Excel.
- 🔒 **أمان متقدم:** تشفير كلمات المرور، حماية من الاختراق (Rate Limiting)، ونظام أدوار.

## 🏗️ هيكل المشروع
```text
├── app.py                  # الواجهة الرئيسية
├── auth.py                 # المصادقة والجلسات
├── database.py             # الاتصال بقاعدة البيانات (Neon)
├── ai_engine.py            # محرك الذكاء الاصطناعي (Groq/Llama 3)
├── gsheets_integration.py  # التكامل مع Google Sheets
├── pages/                  # صفحات إضافية (لوحة المدير)
└── requirements.txt        # المكتبات المطلوبة
