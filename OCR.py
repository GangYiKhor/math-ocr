from functools import cmp_to_key
from pathlib import Path
from PIL import Image
import json
import re

import pytesseract


class Settings:
	TESSERACT_PATH: str
	TIMEOUT: int
	OUTPUT_TYPE: str
	LANG: str
	COMBINE: bool
	CLEAR_OUTPUT: bool
	PRINT_TEXT: bool

	DATATYPES = {
		'int': int,
		'float': float,
		'bool': lambda x: x.upper() == 'TRUE',
		'json': json.loads,
	}

	def __init__(self, settings_file):
		with open(settings_file) as file:
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


class Sorter:
	@cmp_to_key
	@staticmethod
	def compare_path(parts_1: list[str], parts_2: list[str]) -> int:
		parts_1 = parts_1[1:]
		parts_2 = parts_2[1:]
		len_1 = len(parts_1)
		len_2 = len(parts_2)
		for i in range(min(len_1, len_2)):
			if parts_1[i].isnumeric() and parts_2[i].isnumeric():
				num_1 = int(parts_1[i])
				num_2 = int(parts_2[i])
				if num_1 == num_2:
					continue
				else:
					return num_1 - num_2
			elif parts_1[i].isnumeric():
				return 1
			elif parts_2[i].isnumeric():
				return -1
			elif parts_1[i] != parts_2[i]:
				return 1 if parts_1[i] > parts_2[i] else -1
		return 0

	@staticmethod
	def sort_paths(paths: list[Path]) -> list[Path]:
		stems = []
		for path in paths:
			stem = path.stem
			string_parts = re.split(r'\d+', stem)
			number_parts = re.findall(r'\d+', stem)
			number_parts = [''] if len(number_parts) == 0 else number_parts

			parts = [path]
			if string_parts[-1] == '':
				string_parts = string_parts[:-1]
			for i in range(len(string_parts)):
				if string_parts[i] != '':
					parts.append(string_parts[i])
				parts.append(number_parts[i])
			stems.append(parts)

		stems = sorted(stems, key=Sorter.compare_path)
		stems = [stem[0] for stem in stems]
		return stems


def main():
	settings = Settings('./settings.cfg')
	pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
	print('Available languages:', pytesseract.get_languages(config=''))

	input_path = Path('./images')
	all_images = list(input_path.glob('*.png')) + list(input_path.glob('*.jpg')) + list(input_path.glob('*.jpeg'))
	all_images = Sorter.sort_paths(all_images)
	output_path = Path('./output')
	output_path.mkdir(parents=True, exist_ok=True)
	output_file = 'output' if settings.COMBINE else None

	if settings.CLEAR_OUTPUT:
		[file.unlink() for file in output_path.glob('*')]

	for file in all_images:
		print(f'Processing {file.name}')
		write_file = file.stem if output_file is None else output_file

		image = Image.open(file)
		extracted_text = ''

		match (settings.OUTPUT_TYPE):
			case 'TEXT':
				extracted_text = pytesseract.image_to_string(image, timeout=settings.TIMEOUT, lang=settings.LANG)
				with open(output_path / f'{write_file}.txt', 'a' if settings.COMBINE else 'w', encoding='utf-8') as file:
					file.write(extracted_text)

			case 'PDF':
				pdf = pytesseract.image_to_pdf_or_hocr(image, timeout=settings.TIMEOUT, lang=settings.LANG, extension='pdf')
				with open(output_path / f'{write_file}.pdf', 'ab' if settings.COMBINE else 'wb') as file:
					file.write(pdf)

		if settings.PRINT_TEXT and extracted_text:
			print(extracted_text)


if __name__ == '__main__':
	main()
