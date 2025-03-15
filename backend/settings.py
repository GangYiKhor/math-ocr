import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

ENV_TESS_PATH = os.getenv('TESSERACT_PATH', 'Tesseract-OCR/tesseract.exe')

if os.getenv('TESSERACT_PATH_RELATIVE', 'true') == 'true':
	TESSERACT_PATH = BASE_DIR / ENV_TESS_PATH
else:
	TESSERACT_PATH = Path(ENV_TESS_PATH)
