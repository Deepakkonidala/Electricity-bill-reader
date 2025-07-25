from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
import os
import fitz  # PyMuPDF
import pandas as pd
from datetime import datetime
import uuid
import re
from PIL import Image
import pytesseract

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='your-secret-key')

UPLOAD_DIR = "uploads"
RAW_DIR = os.path.join(UPLOAD_DIR, "raw")
MASTER_EXCEL_PATH = os.path.join(UPLOAD_DIR, "usage_data.xlsx")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)

templates = Jinja2Templates(directory="templates")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

users_db = {}
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_USERNAME = "Konidala"
ADMIN_PASSWORD = "Konidala@765"

# Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
async def post_register(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users_db:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username already exists."
        })
    users_db[username] = {"hashed_password": pwd_context.hash(password)}
    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse(url="/admin", status_code=303)

    user = users_db.get(username)
    if not user or not pwd_context.verify(password, user["hashed_password"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid credentials"
        })

    request.session["user"] = username
    return RedirectResponse(url="/upload", status_code=303)

@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("upload.html", {"request": request, "username": request.session["user"]})

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=303)

    # Save raw file
    raw_filename = f"{request.session['user']}_{uuid.uuid4()}_{file.filename}"
    raw_path = os.path.join(RAW_DIR, raw_filename)
    with open(raw_path, "wb") as raw_file:
        contents = await file.read()
        raw_file.write(contents)

    # Temp save for parsing
    temp_pdf_path = os.path.join(UPLOAD_DIR, f"temp_{uuid.uuid4()}.pdf")
    with open(temp_pdf_path, "wb") as f:
        f.write(contents)

    doc = fitz.open(temp_pdf_path)
    text = "".join([page.get_text() for page in doc])
    doc.close()

    if not text.strip():
        doc = fitz.open(temp_pdf_path)
        text_ocr = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text_ocr += pytesseract.image_to_string(img)
        doc.close()
        text = text_ocr

    os.remove(temp_pdf_path)

    # Usage extraction
    usage_value = None
    match_kwh = re.search(r"(\d{1,8}(?:\.\d{1,2})?)\s*(kwh|kilowatt[-\s]?hours?|units|kwhr|kw-h)", text, re.IGNORECASE)
    match_gal = re.search(r"(\d{1,8}(?:\.\d{1,2})?)\s*(gallons?|gl|gal|liters|l|m3|cubic meters)", text, re.IGNORECASE)

    if match_kwh:
        usage_value = f"{match_kwh.group(1)} kWh"
    elif match_gal:
        usage_value = f"{match_gal.group(1)} gallons"

    # Prepare row to append
    excel_data = {
        "username": request.session["user"],
        "filename": file.filename,
        "extracted_usage": usage_value or "N/A",
        "full_text": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Append to master Excel file
    df_new = pd.DataFrame([excel_data])
    if os.path.exists(MASTER_EXCEL_PATH):
        df_existing = pd.read_excel(MASTER_EXCEL_PATH, engine="openpyxl")
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_excel(MASTER_EXCEL_PATH, index=False, engine="openpyxl")

    return templates.TemplateResponse("upload.html", {
        "request": request,
        "username": request.session["user"],
        "message": "File uploaded successfully.",
        "extracted_text": usage_value or ""
    })

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse(url="/login", status_code=303)

    excel_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".xlsx")]
    raw_files = [f"raw/{f}" for f in os.listdir(RAW_DIR) if f.endswith(".pdf")]

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "excel_files": excel_files,
        "raw_files": raw_files
    })

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
