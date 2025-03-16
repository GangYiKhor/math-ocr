import mimetypes
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from sqlmodel import Session, select

from backend.createuser import check_password
from backend.models import (
	User,
	UserSession,
	create_db_and_tables,
	create_user,
	create_user_session,
	engine,
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


def user_context(request: Request):
	with Session(engine) as db_session:
		session_id = request.cookies.get('session_id')
		if session_id is None:
			return {}

		session = select(UserSession).where(UserSession.session_id == session_id)
		session = db_session.exec(session).first()
		if session is None or not session.is_valid():
			return {}

		return {
			'admin': session.user.admin,
			'user': {'full_name': session.user.full_name, 'username': session.user.username},
			'csrf_token': session.csrf_token,
		}


@asynccontextmanager
async def lifespan(app: FastAPI):
	create_db_and_tables()
	yield


async def verify_csrf(db_session: SessionDep, csrf_token: Annotated[str, Form()] = None):
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


async def verify_admin(
	db_session: SessionDep,
	session_id: Annotated[str | None, Cookie()] = None,
	csrf_token: Annotated[str, Form()] = None,
):
	query = select(UserSession).where(UserSession.session_id == session_id).where(UserSession.csrf_token == csrf_token)
	user_session = db_session.exec(query).first()

	if user_session is None or not user_session.is_valid() or not user_session.user.admin:
		raise HTTPException(status_code=404)

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
templates = Jinja2Templates(directory=APP_DIR / 'templates', context_processors=[dev_context, user_context])


class InputType(str, Enum):
	EN_TEXT = 'en_text'
	MS_TEXT = 'ms_text'
	EN_MS_TEXT = 'en_ms_text'
	TEXT = 'text'
	TEXT_FORMULA = 'text_formula'


@app.get('/')
async def root(request: Request, user_session: Annotated[UserSession, Depends(get_session)]):
	if user_session is not None and user_session.is_valid():
		return templates.TemplateResponse(request, name='index.html')
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


# Admin
@app.get('/admin')
async def admin_page(
	request: Request,
	user_session: Annotated[UserSession, Depends(get_session)],
	db_session: SessionDep,
):
	if user_session is None or not user_session.is_valid() or not user_session.user.admin:
		raise HTTPException(status_code=404)

	users = select(User).where(User.username != user_session.user.username)
	users = db_session.exec(users).all()
	users = [user.model_dump() for user in users]

	return templates.TemplateResponse(request=request, name='admin.html', context={'users': users})


@app.post('/admin', dependencies=[Depends(verify_admin)])
async def admin(
	request: Request,
	user_session: Annotated[UserSession, Depends(get_session)],
	user: Annotated[str, Form()],
	status: Annotated[bool, Form()],
	db_session: SessionDep,
):
	update_user = select(User).where(User.username == user)
	update_user = db_session.exec(update_user).first()
	update_user.is_activated = status
	db_session.add(update_user)
	db_session.commit()

	users = select(User).where(User.username != user_session.user.username)
	users = db_session.exec(users).all()
	users = [user.model_dump() for user in users]

	return templates.TemplateResponse(request=request, name='admin.html', context={'users': users})


# Authentications
@app.get('/login')
async def login_page(request: Request):
	return templates.TemplateResponse(request=request, name='login.html')


@app.get('/register')
async def register_page(request: Request):
	return templates.TemplateResponse(request=request, name='register.html')


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
			context={
				'form_error': ['Invalid username or password!'],
				'username': username,
				'password': password,
			},
		)

	if not user.is_activated:
		return templates.TemplateResponse(
			request=request,
			name='login.html',
			context={
				'form_error': ['Account not activated yet! Please contact admin!'],
				'username': username,
				'password': password,
			},
		)

	response = RedirectResponse('/', 302)
	user_session = create_user_session(user, db_session)
	max_age = (user_session.expiration - datetime.now()).total_seconds()
	response.set_cookie('session_id', user_session.session_id, max_age=max_age, secure=True, samesite='strict')
	response.set_cookie('csrf_token', user_session.csrf_token, max_age=max_age, secure=True, samesite='strict')

	return response


@app.post('/register')
async def register(
	request: Request,
	full_name: Annotated[str, Form()],
	username: Annotated[str, Form()],
	password: Annotated[str, Form()],
	db_session: SessionDep,
):
	existing_user = select(User).where(User.username == username)
	existing_user = db_session.exec(existing_user).first()

	if existing_user is not None:
		return templates.TemplateResponse(
			request=request,
			name='register.html',
			context={
				'form_error': ['Username taken!'],
				'full_name': full_name,
				'username': username,
				'password': password,
			},
		)

	try:
		check_password(password)
	except ValueError as error:
		return templates.TemplateResponse(
			request=request,
			name='register.html',
			context={
				'form_error': str(error).split('\n'),
				'full_name': full_name,
				'username': username,
				'password': password,
			},
		)

	password = User.hash_password(password)
	user = User(username=username, full_name=full_name, password=password)
	create_user(user, db_session)

	return templates.TemplateResponse(
		request=request,
		name='register.html',
		context={'success_msg': 'Account applied, please wait for approval!'},
	)


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
