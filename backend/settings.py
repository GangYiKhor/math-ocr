import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
VITE_DEV_URL = os.getenv('VITE_DEV_URL', 'http://localhost:5173')

ENV_TESS_PATH = os.getenv('TESSERACT_PATH', '/bin/tesseract')

if os.getenv('TESSERACT_PATH_RELATIVE', 'false') == 'true':
	TESSERACT_PATH = BASE_DIR / ENV_TESS_PATH
else:
	TESSERACT_PATH = Path(ENV_TESS_PATH)

LOGGING_CONFIG = {
	'version': 1,
	'disable_existing_loggers': True,
	'formatters': {
		'standard': {'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'},
	},
	'handlers': {
		'default': {
			'formatter': 'standard',
			'class': 'logging.StreamHandler',
			'stream': 'ext://sys.stdout',  # Default is stderr
		},
		'file_handler': {
			'formatter': 'standard',
			'class': 'logging.handlers.RotatingFileHandler',
			'filename': 'app.log',
			'maxBytes': 1024 * 1024 * 1,  # = 1MB
			'backupCount': 3,
		},
	},
	'loggers': {
		'uvicorn': {'handlers': ['default', 'file_handler'], 'level': 'TRACE', 'propagate': False},
		'uvicorn.access': {'handlers': ['default', 'file_handler'], 'level': 'TRACE', 'propagate': False},
		'uvicorn.error': {'handlers': ['default', 'file_handler'], 'level': 'TRACE', 'propagate': False},
		'uvicorn.asgi': {'handlers': ['default', 'file_handler'], 'level': 'TRACE', 'propagate': False},
	},
}
