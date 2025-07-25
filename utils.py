import pdfplumber
import os
import pandas as pd

EXCEL_PATH = "excel_data/bills.xlsx"

def extract_data_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    if "kWh" in text:
        for line in text.splitlines():
            if "kWh" in line:
                return ("electricity", extract_number(line))
    elif "gallon" in text.lower():
        for line in text.splitlines():
            if "gallon" in line.lower():
                return ("water", extract_number(line))
    return (None, None)

def extract_number(text):
    import re
    numbers = re.findall(r"[\d,.]+", text)
    return float(numbers[0].replace(",", "")) if numbers else None

def append_to_excel(username, bill_type, value):
    df_new = pd.DataFrame([[username, bill_type, value]],
                          columns=["Username", "Type", "Usage"])
    
    if not os.path.exists(EXCEL_PATH):
        df_new.to_excel(EXCEL_PATH, index=False)
    else:
        df = pd.read_excel(EXCEL_PATH)
        df = pd.concat([df, df_new], ignore_index=True)
        df.to_excel(EXCEL_PATH, index=False)
