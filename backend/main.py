from io import BytesIO
from pathlib import Path
from typing import Annotated

from PIL import Image
from fastapi import FastAPI, Form, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ocr import Settings, analyse_tesseract, analyse_p2t, convert_output
from ocr.p2t import P2TOutput


APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
app = FastAPI()


app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
async def analyse(file: UploadFile):
	try:
		image = Image.open(BytesIO(await file.read()))
		results = analyse_p2t(image, output_type=[P2TOutput.LATEX, P2TOutput.OMML, P2TOutput.MATHML])
		results[P2TOutput.LATEX.value] = [result.strip() for result in results[P2TOutput.LATEX.value] if result.strip() != '']

		return { 'output': {
			'latex': results[P2TOutput.LATEX.value],
			'omml': results[P2TOutput.OMML.value],
			'mathml': results[P2TOutput.MATHML.value],
		}}
	except Exception:
		return Response('Failed to analyse! Image too complex!', 422)


@app.post('/download')
async def download(latex: Annotated[list[str], Form()]):
	try:
		stream = convert_output(latex, output_type=P2TOutput.DOCX)
		stream.seek(0)
		return StreamingResponse(stream, media_type='application/octet', headers={'Content-Disposition': 'attachment; filename="math-ocr.docx"'})
	except Exception:
		return Response('Invalid LaTeX!', 400)
