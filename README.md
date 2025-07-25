# 🌱 PDF Bill Upload and Usage Extraction Web App (FastAPI)

A FastAPI-based web application that allows users to upload electricity or water bill PDFs. The system extracts usage data (like kWh or gallons) from each PDF and logs all uploads in a single, centralized Excel file. Admin users can view both raw uploaded files and the compiled Excel log through a dashboard.

---

## 🚀 Features

- 👤 User registration and login system
- 🔐 Admin login with access to a file dashboard
- 📄 Upload electricity or water bill PDFs
- 🧠 Extract text using PyMuPDF or Tesseract OCR (fallback)
- 🔎 Regex-based pattern matching to detect kWh/gallon usage
- 📊 All uploads logged into a single Excel file (`uploads/combined_data.xlsx`)
- 🗂 Admin dashboard to view all Excel and raw PDF uploads

---

## 🛠 Tech Stack

- **Backend:** FastAPI
- **Templating:** Jinja2
- **PDF Handling:** PyMuPDF (`fitz`), Tesseract OCR (`pytesseract`)
- **Data Storage:** Pandas + Excel (`openpyxl`)
- **Session Management:** Starlette Middleware
- **Password Hashing:** Passlib (bcrypt)

---