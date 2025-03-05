from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Annotated

from PIL import Image
from fastapi import FastAPI, Form, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ocr import Settings, analyse_tesseract, analyse_p2t, convert_output
from ocr.p2t import P2TOutput

origins = ['*']
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InputType(str, Enum):
	EN_TEXT = 'en_text'
	MS_TEXT = 'ms_text'
	EN_MS_TEXT = 'en_ms_text'
	TEXT = 'text'
	TEXT_FORMULA = 'text_formula'


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


@app.post('/analyse')
async def analyse(file: Annotated[UploadFile, Form()], analysis_type: Annotated[InputType, Form()], response: Response):
	try:
		image = Image.open(BytesIO(await file.read()))
	except Exception:
		response.status_code = 415
		return { 'error': 'Invalid Image!' }

	if analysis_type in [InputType.EN_TEXT, InputType.MS_TEXT, InputType.EN_MS_TEXT]:
		settings = {
			'TESSERACT_PATH': BASE_DIR / 'Tesseract-OCR' / 'tesseract.exe',
			'TIMEOUT': 0,
			'OUTPUT_TYPE': 'TEXT',
			'COMBINE': True,
			'CLEAR_OUTPUT': True,
			'PRINT_TEXT': False,
		}
		if analysis_type == InputType.EN_TEXT:
			settings['LANG'] = 'eng'
		elif analysis_type == InputType.MS_TEXT:
			settings['LANG'] = 'msa'
		elif analysis_type == InputType.EN_MS_TEXT:
			settings['LANG'] = 'eng+msa'
		settings = Settings(settings)

		result_tesseract = analyse_tesseract(settings, image)
		return { 'output': { 'latex': result_tesseract }}

	try:
		results = analyse_p2t(image, analysis_type, [P2TOutput.LATEX, P2TOutput.OMML, P2TOutput.MATHML])
		results[P2TOutput.LATEX.value] = [result.strip() for result in results[P2TOutput.LATEX.value] if result.strip() != '']

		return { 'output': {
			'latex': results[P2TOutput.LATEX.value],
			'omml': results[P2TOutput.OMML.value],
			'mathml': results[P2TOutput.MATHML.value],
		}}
	except Exception:
		response.status_code = 422
		return { 'error': 'Failed to analyse! Image too complex!' }


@app.post('/download')
async def download(latex: Annotated[list[str], Form()], response: Response):
	try:
		stream = convert_output(latex, output_type=P2TOutput.DOCX)
		stream.seek(0)
		return StreamingResponse(stream, media_type='application/octet', headers={'Content-Disposition': 'attachment; filename="math-ocr.docx"'})
	except Exception:
		response.status_code = 400
		return { 'error': 'Invalid LaTeX!' }
