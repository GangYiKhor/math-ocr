import mimetypes
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from sqlmodel import Session, select

from backend.models import (
	User,
	UserSession,
	create_db_and_tables,
	create_user_session,
	get_db_session,
)
from backend.settings import TESSERACT_PATH, VITE_DEV_URL
from ocr import P2TOutput, Settings, analyse_p2t, analyse_tesseract, convert_output

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DEV_MODE = '--reload' in sys.argv or 'dev' in sys.argv

mimetypes.init()
mimetypes.add_type('application/javascript', '.js')


SessionDep = Annotated[Session, Depends(get_db_session)]


def dev_context(request: Request):
	return {'DEV_MODE': DEV_MODE, 'DEV_VITE_URL': VITE_DEV_URL}


@asynccontextmanager
async def lifespan(app: FastAPI):
	create_db_and_tables()
	yield


async def verify_csrf(
	db_session: SessionDep,
	csrf_token_header: Annotated[str, Header(alias='X-CSRFToken')] = None,
	csrf_token_form: Annotated[str, Form(alias='csrf_token')] = None,
):
	csrf_token = csrf_token_header if csrf_token_header is not None else csrf_token_form
	query = select(UserSession).where(UserSession.csrf_token == csrf_token)
	user_session = db_session.exec(query).first()

	if user_session is None or not user_session.is_valid():
		raise HTTPException(status_code=401, detail='User not logged in!')

	return user_session


async def verify_session(db_session: SessionDep, session_id: Annotated[str | None, Cookie()] = None):
	query = select(UserSession).where(UserSession.session_id == session_id)
	user_session = db_session.exec(query).first()

	if user_session is None or not user_session.is_valid():
		raise HTTPException(status_code=401, detail='User not logged in!')

	return user_session


async def get_session(db_session: SessionDep, session_id: Annotated[str | None, Cookie()] = None):
	query = select(UserSession).where(UserSession.session_id == session_id)
	user_session = db_session.exec(query).first()
	return user_session


async def get_csrf(
	db_session: SessionDep,
	csrf_token: Annotated[str | None, Form()] = None,
	session_id: Annotated[str | None, Cookie()] = None,
):
	query = select(UserSession).where(UserSession.csrf_token == csrf_token).where(UserSession.session_id == session_id)
	user_session = db_session.exec(query).first()
	return user_session


app = FastAPI(lifespan=lifespan)
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

app.mount('/static', StaticFiles(directory=APP_DIR / 'static'), name='static')
templates = Jinja2Templates(directory=APP_DIR / 'templates', context_processors=[dev_context])


class InputType(str, Enum):
	EN_TEXT = 'en_text'
	MS_TEXT = 'ms_text'
	EN_MS_TEXT = 'en_ms_text'
	TEXT = 'text'
	TEXT_FORMULA = 'text_formula'


@app.get('/')
async def root(request: Request, user_session: Annotated[UserSession, Depends(get_session)]):
	if user_session is not None and user_session.is_valid():
		return templates.TemplateResponse(
			request,
			name='index.html',
			context={
				'csrf_token': user_session.csrf_token,
				'username': user_session.user.full_name,
			},
		)
	else:
		return RedirectResponse('/login', 302)


@app.post('/analyse', dependencies=[Depends(verify_session), Depends(verify_csrf)])
async def analyse(
	file: Annotated[UploadFile, Form()],
	analysis_type: Annotated[InputType, Form()],
	response: Response,
):
	try:
		image = Image.open(BytesIO(await file.read()))
	except Exception:
		response.status_code = 415
		return {'error': 'Invalid Image!'}

	if analysis_type in [InputType.EN_TEXT, InputType.MS_TEXT, InputType.EN_MS_TEXT]:
		settings = {
			'TESSERACT_PATH': TESSERACT_PATH,
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
		return {'output': {'latex': result_tesseract}}

	try:
		results = analyse_p2t(image, analysis_type, [P2TOutput.LATEX, P2TOutput.OMML, P2TOutput.MATHML])
		results[P2TOutput.LATEX.value] = [
			result.strip() for result in results[P2TOutput.LATEX.value] if result.strip() != ''
		]

		return {
			'output': {
				'latex': results[P2TOutput.LATEX.value],
				'omml': results[P2TOutput.OMML.value],
				'mathml': results[P2TOutput.MATHML.value],
			}
		}
	except Exception:
		response.status_code = 422
		return {'error': 'Failed to analyse! Image too complex!'}


@app.post('/download', dependencies=[Depends(verify_session), Depends(verify_csrf)])
async def download(
	latex: Annotated[list[str], Form()],
	response: Response,
):
	try:
		stream = convert_output(latex, output_type=P2TOutput.DOCX)
		stream.seek(0)
		return StreamingResponse(
			stream,
			media_type='application/octet',
			headers={'Content-Disposition': 'attachment; filename="math-ocr.docx"'},
		)
	except Exception:
		response.status_code = 400
		return {'error': 'Invalid LaTeX!'}


# Authentications
@app.get('/login')
async def login_page(request: Request):
	return templates.TemplateResponse(request=request, name='login.html')


@app.post('/login')
async def login(
	request: Request,
	username: Annotated[str, Form()],
	password: Annotated[str, Form()],
	response: Response,
	db_session: SessionDep,
):
	user = select(User).where(User.username == username)
	user = db_session.exec(user).first()

	if user is None or not user.check_password(password):
		return templates.TemplateResponse(
			request=request,
			name='login.html',
			context={'form_error': 'Invalid username or password!'},
		)

	response = RedirectResponse('/', 302)
	user_session = create_user_session(user, db_session)
	max_age = (user_session.expiration - datetime.now()).total_seconds()
	response.set_cookie('session_id', user_session.session_id, max_age=max_age, secure=True, samesite='strict')
	response.set_cookie('csrf_token', user_session.csrf_token, max_age=max_age, secure=True, samesite='strict')

	return response


@app.get('/csrf')
async def csrf(user_session: Annotated[UserSession, Depends(get_session)], response: Response):
	if user_session is not None and user_session.is_valid():
		return {'csrf_token': user_session.csrf_token}
	else:
		response.status_code = 401
		return {'error': 'User not logged in!'}


@app.post('/logout')
async def logout(user_session: Annotated[UserSession, Depends(get_csrf)], db_session: SessionDep, response: Response):
	if user_session is not None:
		user_session.is_revoked = True
		db_session.add(user_session)
		db_session.commit()

		response = RedirectResponse('/login', 302)
		response.delete_cookie('session_id')
		response.delete_cookie('csrf_token')

		return response
	else:
		response.status_code = 401
		return {'error': 'Not authorised!'}
