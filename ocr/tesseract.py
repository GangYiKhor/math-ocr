from pathlib import Path
import json

from PIL import Image
from PIL.Image import Image as ImageType
import pytesseract


FILE_DIR = Path(__file__).resolve().parent
BASE_DIR = FILE_DIR.parent


class Settings:
	TESSERACT_PATH: str
	TIMEOUT: int
	LANG: str
	DATATYPES = {
		'int': int,
		'float': float,
		'bool': lambda x: x.upper() == 'TRUE',
		'json': json.loads,
	}

	def __init__(self, settings: dict = None):
		if settings is None:
			return

		for (key, value) in settings.items():
			setattr(self, key, value)

	def read_config_file(self, config_file: Path):
		with open(config_file) as file:
			lines = file.readlines()

			for line in lines:
				line = line.removesuffix('\n').removesuffix('\r')
				[key, value] = line.split('=')
				value = value.removeprefix('"').removesuffix('"')

				if value.startswith('<') and '>' in value:
					datatype = value.split('>')[0].removeprefix('<')
					value = value.split('>')[1]

					if datatype in self.DATATYPES:
						value = self.DATATYPES[datatype](value)

				setattr(self, key, value)


def analyse_tesseract(settings: Settings, images: list[ImageType] | ImageType):
	pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

	if not isinstance(images, list):
		images = [images]

	output = []
	for image in images:
		output.append(pytesseract.image_to_string(image, timeout=settings.TIMEOUT, lang=settings.LANG))

	return output
