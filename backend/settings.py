from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
TESSERACT_PATH = BASE_DIR / 'Tesseract-OCR' / 'tesseract.exe'
