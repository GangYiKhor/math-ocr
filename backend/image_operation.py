from io import BytesIO
from typing import Tuple

from PIL import Image, ImageChops
from PIL.Image import Image as ImageType


def convert_to_jpeg(image: ImageType):
	with BytesIO() as mem:
		image = image.convert(mode='RGB')
		image.save(mem, format='JPEG')
		image = Image.open(mem)
		return image.copy()


def crop_image(image: ImageType, colour: Tuple[int, int, int] = (255, 255, 255), threshold=50):
	bg = Image.new(mode='RGB', size=image.size, color=colour)
	diff = ImageChops.difference(image, bg)
	diff = ImageChops.add(diff, diff, 2.0, -threshold)
	bbox = diff.getbbox()
	if bbox:
		return image.crop(bbox)
	else:
		return None
