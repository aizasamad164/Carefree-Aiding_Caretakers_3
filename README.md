# No external libraries needed for a simple README.md, but following instructions to generate files.

readme_content = """<div align="center">
<img src="./static/logo.svg" width="400" alt="Carefree Logo" />

# Carefree — Modular Oracle Edition
### Smart Caretaker Management & Health Predictive Analytics

<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/Oracle_DB-F80000?style=for-the-badge&logo=oracle&logoColor=white" />
<img src="https://img.shields.io/badge/Scikit--Learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" />

<br/>

**The "Peace of Mind" Platform for Caregiving.** Bridging the gap between daily patient care and intelligent health forecasting using Oracle's robust database engine.

[🚀 Explore API Docs](http://localhost:8000/docs)
</div>

---

## 🏥 The Carefree Ecosystem
Carefree is a **Role-Based Healthcare Hub** designed to streamline communication and predict medical needs before they become emergencies.

* **Caretakers:** Manage daily tasks, medication logs, and medical appointments.
* **Guardians:** Remote monitoring of patient well-being, financial expenses, and health trends.
* **ML Engine:** Analyzes lifestyle data to forecast stress levels and insurance costs.

---

## 🚀 Key Modules

| Portal | User Persona | Key Capabilities | Visual Vibe |
| :--- | :--- | :--- | :--- |
| **🏠 Dashboard** | Caretakers | • **Task CRUD:** Real-time patient needs.<br>• **Appointments:** Synchronized scheduling.<br>• **Notifications:** Critical task alerts. | 🩺 Clinical |
| **🛡️ Guardian** | Family/Legal | • **Expense Tracking:** Monitor care spending.<br>• **Health Logs:** Historical patient progress.<br>• **Access Control:** Secure data monitoring. | 🛡️ Secure |
| **🧠 Predictor** | Analysts | • **Stress ML:** Predicts stress via lifestyle data.<br>• **Cost ML:** Estimates medical insurance costs. | 🧪 Analytical |

---

## 🛠️ Installation & Setup

### 1. Environment Configuration
Edit `config.py` to match your Oracle Database credentials:
```python
USE_CLOUD   = False         # True for Oracle Cloud (ADB)
DB_HOST     = "localhost"
DB_PORT     = 1521
DB_SERVICE  = "XEPDB1"
DB_USER     = "carefree"
DB_PASSWORD = "carefree123"
