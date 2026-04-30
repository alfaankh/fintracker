from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os
import json
from parser import parse_document
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="FinTracker Parser API")

# Allow Next.js to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "FinTracker Parser API running ✅"}

@app.post("/parse")
async def parse_file(
    file: UploadFile = File(...),
    uploaded_by: str = Form(default="fan")
):
    # Save uploaded file temporarily
    suffix = '.' + file.filename.split('.')[-1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = parse_document(tmp_path, file.filename)
        result['uploaded_by'] = uploaded_by
        return result
    finally:
        os.unlink(tmp_path)

@app.post("/parse-text")
async def parse_text(data: dict):
    text = data.get('text', '')
    sender = data.get('sender', 'fan')
    
    # Quick transaction parser for natural text
    # "beli ayam 10rb" → transaction
    import re
    
    amount_patterns = [
        r'(\d+(?:[.,]\d+)?)\s*(?:rb|ribu|k)',
        r'(\d+(?:[.,]\d+)?)\s*(?:jt|juta)',
        r'rp\.?\s*(\d+(?:[.,]\d+)*)',
        r'(\d{4,})'
    ]
    
    amount = 0
    for pattern in amount_patterns:
        match = re.search(pattern, text.lower())
        if match:
            num = match.group(1).replace(',', '').replace('.', '')
            amount = float(num)
            if 'rb' in text.lower() or 'ribu' in text.lower() or 'k' in text.lower():
                amount *= 1000
            elif 'jt' in text.lower() or 'juta' in text.lower():
                amount *= 1000000
            break
    
    if amount == 0:
        return {"parsed": False, "message": "No amount detected"}
    
    # Detect type
    income_words = ['gaji', 'salary', 'terima', 'masuk', 'dapat', 'bayaran']
    txn_type = 'income' if any(w in text.lower() for w in income_words) else 'expense'
    
    # Clean description
    description = re.sub(r'\d+(?:[.,]\d+)?\s*(?:rb|ribu|k|jt|juta)?', '', text).strip()
    description = re.sub(r'rp\.?\s*[\d.,]+', '', description).strip()
    description = ' '.join(description.split())
    
    from datetime import date
    
    return {
        "parsed": True,
        "transaction": {
            "date": date.today().isoformat(),
            "description": description or text,
            "amount": amount,
            "amount_idr": amount,
            "currency": "IDR",
            "type": txn_type,
            "source": "text",
            "spent_by": sender
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)