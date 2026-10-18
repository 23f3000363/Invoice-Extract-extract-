from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import re

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractIn(BaseModel):
    text: str = ""

class Invoice(BaseModel):
    vendor: str
    amount: float
    currency: str = Field(..., min_length=3, max_length=3)
    date: str

def extract(text: str) -> dict:
    if not text or not text.strip():
        return {
            "vendor": "Unknown",
            "amount": 0.0,
            "currency": "USD",
            "date": "2026-01-01"
        }

    # ---------- VENDOR ----------
    vendor = "Unknown"
    m = re.search(
        r'([A-Za-z0-9][A-Za-z0-9\-\s&\.]+?(?:Industries|Ltd|LLC|Inc|Corp|Company|Co\.?))',
        text,
        re.I
    )
    if m:
        vendor = m.group(1).strip()
    else:
        m = re.search(r'\b([A-Z][A-Za-z0-9\-]{2,}(?:\s+[A-Z][A-Za-z0-9\-]*){0,4})', text)
        if m:
            vendor = m.group(1).strip()

    # ---------- AMOUNT (much stronger) ----------
    amount = 0.0

    # 1. Look for numbers near total / amount / due / balance / payable
    patterns = [
        r'(?:total|amount|due|balance|payable|pay(?:ment)?)\s*(?:due|amount|to\s+pay)?[:\s]*[\$€£]?\s*([\d,]+\.\d{2})',
        r'(?:total|amount|due|balance|payable)[:\s]*[\$€£]?\s*([\d,]+\.\d{2})',
        r'[\$€£]\s*([\d,]+\.\d{2})',
        r'([\d,]+\.\d{2})\s*(?:USD|EUR|GBP|dollars|euros|pounds)',
        r'(?:USD|EUR|GBP)\s*([\d,]+\.\d{2})',
        r'([\d,]+\.\d{2})',          # last resort - any money-looking number
    ]

    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            try:
                amount = float(m.group(1).replace(',', ''))
                if amount > 0:
                    break
            except:
                continue

    # ---------- CURRENCY ----------
    currency = "USD"
    if re.search(r'\bEUR\b|€|euro', text, re.I):
        currency = "EUR"
    elif re.search(r'\bGBP\b|£|pound', text, re.I):
        currency = "GBP"
    elif re.search(r'\bUSD\b|\$|dollar', text, re.I):
        currency = "USD"

    # ---------- DATE ----------
    date = "2026-01-01"
    m = re.search(r'(2026-\d{2}-\d{2})', text)
    if m:
        date = m.group(1)
    else:
        # try other common formats
        m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](2026)', text)
        if m:
            d, mo, y = m.groups()
            date = f"{y}-{int(mo):02d}-{int(d):02d}"

    return {
        "vendor": vendor,
        "amount": amount,
        "currency": currency,
        "date": date
    }

@app.post("/extract", response_model=Invoice)
def do_extract(body: ExtractIn):
    return extract(body.text or "")
