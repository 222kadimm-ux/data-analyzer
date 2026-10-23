# 💼 Pro Data Analyzer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://data-analyzer-vzl8jspasawmzxey7gezcm.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered data analysis platform. Upload Excel/CSV files and get instant statistical insights, interactive charts, and AI-generated reports in Arabic.

## ✨ Features
- 🤖 **AI Chat with Data:** Ask questions in natural language (Powered by Llama 3 via OpenRouter).
- 📊 **Advanced Statistics:** Correlation matrix, mean, max, and best-selling products.
- 📝 **Auto-Reports:** One-click AI-generated analytical reports.
- 📥 **Export:** Download results as CSV or Excel.
- 🔒 **Privacy First:** No PII collected. Anonymous usage. (GDPR compliant).

## 🚀 Live Demo
[Try the app here](https://data-analyzer-vzl8jspasawmzxey7gezcm.streamlit.app)

## 🏗️ Architecture
- **Frontend:** Streamlit (Python)
- **Database:** Neon (PostgreSQL)
- **AI Engine:** OpenRouter (Llama 3)
- **Monitoring:** Sentry

## 🛠️ Local Setup
1. Clone the repo: `git clone https://github.com/222kadimm-ux/data-analyzer.git`
2. Install requirements: `pip install -r requirements.txt`
3. Add secrets in `.streamlit/secrets.toml`
4. Run: `streamlit run app.py`
