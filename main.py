from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ExtractIn(BaseModel):
    text: str = ""

class Invoice(BaseModel):
    vendor: str
    amount: float
    currency: str = Field(..., min_length=3, max_length=3)
    date: str

def extract(text: str) -> dict:
    if not text.strip():
        return {"vendor": "Unknown", "amount": 0.0, "currency": "USD", "date": "2026-01-01"}
    vendor = "Unknown"
    m = re.search(r'([A-Za-z0-9][A-Za-z0-9\-\s&]+?(?:Industries|Ltd|LLC|Inc|Corp|Company|Co\.?))', text, re.I)
    if m: vendor = m.group(1).strip()
    amount = 0.0
    m = re.search(r'(?:total|amount|due|balance|pay(?:ment)?)\s*(?:due)?[:\s]*[\$€£]?\s*([\d,]+\.?\d*)', text, re.I)
    if m: amount = float(m.group(1).replace(',',''))
    currency = "USD"
    if re.search(r'\bEUR\b|€|euro', text, re.I): currency = "EUR"
    elif re.search(r'\bGBP\b|£|pound', text, re.I): currency = "GBP"
    date = "2026-01-01"
    m = re.search(r'(2026-\d{2}-\d{2})', text)
    if m: date = m.group(1)
    return {"vendor": vendor, "amount": amount, "currency": currency, "date": date}

@app.post("/extract", response_model=Invoice)
def do_extract(body: ExtractIn):
    return extract(body.text or "")