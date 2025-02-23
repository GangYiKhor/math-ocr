from pathlib import Path

from PIL import Image
from fastapi import FastAPI

from ocr import Settings, analyse_tesseract, analyse_p2t


APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
app = FastAPI()


@app.get('/')
async def root():
	settings = Settings({
		'TESSERACT_PATH': BASE_DIR / 'Tesseract-OCR' / 'tesseract.exe',
		'TIMEOUT': 0,
		'OUTPUT_TYPE': 'TEXT',
		'LANG': 'eng',
		'COMBINE': True,
		'CLEAR_OUTPUT': True,
		'PRINT_TEXT': False,
	})
	image = Image.open(BASE_DIR / 'images' / 'sqrt-2.3.png')
	result_tesseract = analyse_tesseract(settings, image)
	result_p2t = analyse_p2t(image)

	return {
		'tesseract': result_tesseract,
		'pix2text': result_p2t,
	}
