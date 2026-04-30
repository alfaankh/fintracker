import pdfplumber
import pytesseract
from PIL import Image
import anthropic
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')

claude = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# ── HELPERS ────────────────────────────────────────────────
def clean_amount(amount_str: str) -> float:
    cleaned = amount_str.replace('.', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except:
        return 0.0

def is_valid_date(date_str: str) -> bool:
    months = [
        'jan', 'feb', 'mar', 'apr', 'may', 'mei', 'jun',
        'jul', 'aug', 'agu', 'sep', 'oct', 'okt', 'nov', 'dec', 'des'
    ]
    date_lower = date_str.lower()
    has_month = any(m in date_lower for m in months)
    has_slash = '/' in date_str
    has_dash = re.search(r'\d{2}-\d{2}-\d{4}', date_str)
    return has_month or has_slash or bool(has_dash)

def detect_sign(line: str) -> str:
    if re.search(r'\+\s*[\d,.]', line):
        return 'income'
    if re.search(r'-\s*[\d,.]', line):
        return 'expense'
    line_lower = line.lower()
    if any(w in line_lower for w in ['cr', 'credit', 'masuk', 'received', 'gaji', 'salary', 'incoming']):
        return 'income'
    return 'expense'

# ── BANK DETECTOR ──────────────────────────────────────────
def detect_bank(text: str, filename: str) -> str:
    filename_lower = filename.lower()
    text_lower = text.lower()

    if 'jenius' in filename_lower or 'jenius' in text_lower:
        if 'estatement' in filename_lower:
            return 'jenius_monthly'
        if 'jenius_main_history' in filename_lower or 'main_history' in filename_lower:
            if any(x in text_lower for x in ['cny', 'rmb', 'yuan', '¥', 'renminbi']):
                return 'jenius_rmb'
            return 'jenius_idr'
        if any(x in text_lower for x in ['cny', 'rmb', 'yuan', '¥']):
            return 'jenius_rmb'
        if any(x in text_lower for x in ['flexi saver', 'cashcow', 'cash cow']):
            return 'jenius_monthly'
        return 'jenius_idr'

    if 'bca' in filename_lower or 'bank central asia' in text_lower:
        return 'bca'
    if 'seabank' in filename_lower or 'sea bank' in text_lower:
        return 'seabank'
    if 'mandiri' in filename_lower or 'bank mandiri' in text_lower:
        return 'mandiri'
    if 'icbc' in filename_lower or 'icbc' in text_lower:
        return 'icbc'
    if 'gopay' in filename_lower or 'gojek' in text_lower:
        return 'gopay'
    if 'ovo' in filename_lower or 'ovo' in text_lower:
        return 'ovo'
    if 'shopeepay' in filename_lower or 'shopee' in text_lower:
        return 'shopeepay'

    return 'unknown'

# ── PDF TEXT EXTRACTOR ─────────────────────────────────────
def extract_pdf_text(file_path: str) -> str:
    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text

# ── JENIUS MONTHLY PARSER ──────────────────────────────────
def parse_jenius_monthly(text: str) -> list:
    transactions = []
    lines = text.split('\n')

    date_pattern = re.compile(
        r'\b(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Mei|Jun|Jul|Aug|Agu|Sep|Oct|Okt|Nov|Dec|Des)\s+\d{4})\b',
        re.IGNORECASE
    )

    internal_keywords = [
        'flexi saver', 'flexisaver', 'cashcow', 'cash cow',
        'top up rmb', 'beli rmb', 'buy rmb', 'transfer to rmb',
        'transfer antar rekening', 'internal transfer',
        'exchange primary cny', 'exchange primary'
    ]

    weixin_keywords = ['weixin', 'wechat', 'wx pay']

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue

        date_match = date_pattern.search(line)
        if not date_match:
            continue

        date_str = date_match.group(1)
        if not is_valid_date(date_str):
            continue

        amount_match = re.search(r'[\+\-]\s*([\d]+(?:[.,]\d+)*)', line)
        if not amount_match:
            continue

        try:
            amount = clean_amount(amount_match.group(1))
            if amount == 0:
                continue

            description = line[date_match.end():].strip()
            description = re.sub(r'[\+\-]\s*[\d.,]+', '', description).strip()
            description = ' '.join(description.split())[:100]

            line_lower = line.lower()
            is_internal = any(kw in line_lower for kw in internal_keywords)
            is_weixin = any(kw in line_lower for kw in weixin_keywords)
            txn_type = detect_sign(line)

            if is_internal:
                txn_type = 'internal_transfer'

            transactions.append({
                'date': date_str,
                'description': description,
                'amount': amount,
                'amount_idr': amount,
                'currency': 'IDR',
                'type': txn_type,
                'is_internal_transfer': is_internal,
                'is_weixin': is_weixin,
                'source': 'jenius_monthly'
            })
        except:
            continue

    return transactions

# ── JENIUS IDR DYNAMIC PARSER ──────────────────────────────
def parse_jenius_idr(text: str) -> list:
    transactions = []
    lines = text.split('\n')

    date_pattern = re.compile(
        r'\b(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Mei|Jun|Jul|Aug|Agu|Sep|Oct|Okt|Nov|Dec|Des)\s+\d{4})\b',
        re.IGNORECASE
    )

    weixin_keywords = ['weixin', 'wechat', 'wx pay']

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue

        date_match = date_pattern.search(line)
        if not date_match:
            continue

        date_str = date_match.group(1)
        if not is_valid_date(date_str):
            continue

        amount_match = re.search(r'[\+\-]\s*([\d]+(?:[.,]\d+)*)', line)
        if not amount_match:
            continue

        try:
            amount = clean_amount(amount_match.group(1))
            if amount == 0:
                continue

            description = line[date_match.end():].strip()
            description = re.sub(r'[\+\-]\s*[\d.,]+', '', description).strip()
            description = ' '.join(description.split())[:100]

            line_lower = line.lower()
            is_weixin = any(kw in line_lower for kw in weixin_keywords)
            txn_type = detect_sign(line)

            transactions.append({
                'date': date_str,
                'description': description,
                'amount': amount,
                'amount_idr': amount,
                'currency': 'IDR',
                'type': txn_type,
                'is_internal_transfer': False,
                'is_weixin': is_weixin,
                'source': 'jenius_idr'
            })
        except:
            continue

    return transactions

# ── JENIUS RMB PARSER ──────────────────────────────────────
def parse_jenius_rmb(text: str) -> list:
    transactions = []
    lines = text.split('\n')

    date_pattern = re.compile(
        r'\b(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Mei|Jun|Jul|Aug|Agu|Sep|Oct|Okt|Nov|Dec|Des)\s+\d{4})\b',
        re.IGNORECASE
    )

    CNY_TO_IDR = 2230

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue

        date_match = date_pattern.search(line)
        if not date_match:
            continue

        date_str = date_match.group(1)
        if not is_valid_date(date_str):
            continue

        amount_match = re.search(r'[\+\-]\s*(\d+(?:\.\d{1,2})?)|,\s*(\d+(?:\.\d{1,2})?)', line)
        if not amount_match:
            continue

        try:
            raw = amount_match.group(1) or amount_match.group(2)
            amount_cny = float(raw)
            if amount_cny == 0:
                continue

            amount_idr = round(amount_cny * CNY_TO_IDR)

            description = line[date_match.end():].strip()
            description = re.sub(r'[\+\-]\s*[\d.]+', '', description).strip()
            description = re.sub(r',\s*[\d.]+', '', description).strip()
            description = ' '.join(description.split())[:100]

            txn_type = detect_sign(line)
            desc_lower = description.lower().strip()
            is_exchange = desc_lower in ['buy', 'sell']

            transactions.append({
                'date': date_str,
                'description': description,
                'amount': amount_cny,
                'amount_idr': amount_idr,
                'currency': 'CNY',
                'exchange_rate': CNY_TO_IDR,
                'type': 'internal_transfer' if is_exchange else txn_type,
                'is_internal_transfer': is_exchange,
                'is_weixin': True,
                'source': 'jenius_rmb'
            })
        except:
            continue

    return transactions

# ── BCA PARSER ─────────────────────────────────────────────
def parse_bca(text: str) -> list:
    transactions = []
    lines = text.split('\n')

    date_pattern = re.compile(r'(\d{2}/\d{2}|\d{2}-\d{2}-\d{4}|\d{2}/\d{2}/\d{4})')
    amount_pattern = re.compile(r'([\d.]+,\d{2})')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        date_match = date_pattern.search(line)
        if not date_match:
            continue

        amount_matches = amount_pattern.findall(line)
        if not amount_matches:
            continue

        try:
            date_str = date_match.group(1)
            description = line[date_match.end():].strip()

            amount_str = amount_matches[0].replace('.', '').replace(',', '.')
            amount = float(amount_str)

            txn_type = 'expense'
            if 'cr' in line.lower() or 'kredit' in line.lower():
                txn_type = 'income'

            transactions.append({
                'date': date_str,
                'description': description[:100],
                'amount': amount,
                'amount_idr': amount,
                'currency': 'IDR',
                'type': txn_type,
                'is_internal_transfer': False,
                'source': 'bca'
            })
        except:
            continue

    return transactions

# ── AI FALLBACK PARSER ─────────────────────────────────────
def parse_with_ai(text: str, source: str) -> list:
    prompt = f"""You are a financial document parser for Indonesian bank statements.

Extract all transactions from this {source} bank statement.

Return ONLY a JSON array with this exact format:
[
  {{
    "date": "DD/MM/YYYY",
    "description": "transaction description",
    "amount": 50000,
    "currency": "IDR",
    "type": "expense or income",
    "source": "{source}"
  }}
]

Rules:
- date: convert to DD/MM/YYYY format
- amount: number only, no currency symbols
- type: "income" if money came in, "expense" if money went out
- If CNY/RMB amounts, use currency: "CNY"
- Return empty array [] if no transactions found
- Return ONLY the JSON array, nothing else

Bank statement text:
{text[:4000]}"""

    message = claude.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()

    if '```json' in response_text:
        response_text = response_text.split('```json')[1].split('```')[0]
    elif '```' in response_text:
        response_text = response_text.split('```')[1].split('```')[0]

    transactions = json.loads(response_text)

    for txn in transactions:
        if txn.get('currency') == 'CNY':
            txn['amount_idr'] = txn['amount'] * 2230
        else:
            txn['amount_idr'] = txn['amount']
        txn['source'] = source

    return transactions

# ── IMAGE/SCREENSHOT PARSER ────────────────────────────────
def parse_image(file_path: str) -> list:
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang='ind+eng')

    if not text.strip():
        return []

    return parse_with_ai(text, 'screenshot')

# ── MAIN PARSER FUNCTION ───────────────────────────────────
def parse_document(file_path: str, filename: str) -> dict:
    ext = filename.lower().split('.')[-1]
    transactions = []
    bank = 'unknown'

    try:
        if ext == 'pdf':
            text = extract_pdf_text(file_path)
            bank = detect_bank(text, filename)

            if bank == 'jenius_monthly':
                transactions = parse_jenius_monthly(text)
                if len(transactions) < 3:
                    transactions = parse_with_ai(text, bank)

            elif bank == 'jenius_idr':
                transactions = parse_jenius_idr(text)
                if len(transactions) < 3:
                    transactions = parse_with_ai(text, bank)

            elif bank == 'jenius_rmb':
                transactions = parse_jenius_rmb(text)
                if len(transactions) < 3:
                    transactions = parse_with_ai(text, bank)

            elif bank == 'bca':
                transactions = parse_bca(text)
                if len(transactions) < 3:
                    transactions = parse_with_ai(text, bank)

            else:
                transactions = parse_with_ai(text, bank)

        elif ext in ['jpg', 'jpeg', 'png', 'webp']:
            bank = 'screenshot'
            transactions = parse_image(file_path)

        else:
            return {'error': f'Unsupported file type: {ext}'}

        return {
            'bank': bank,
            'filename': filename,
            'transaction_count': len(transactions),
            'transactions': transactions
        }

    except Exception as e:
        return {'error': str(e), 'bank': bank}