from io import BytesIO
from pathlib import Path
from typing import Literal

from docx import Document
from lxml import etree
from PIL import Image
from PIL.Image import Image as ImageType
from pix2text import Pix2Text
import latex2mathml.converter


FILE_DIR = Path(__file__).resolve().parent
BASE_DIR = FILE_DIR.parent


class FormatConverter:
	def __init__(self):
		self.latex_to_mathml = latex2mathml.converter.convert
		self.mathml_to_omml = etree.XSLT(etree.parse(BASE_DIR / 'data' / 'MML2OMML.XSL'))  #NOSONAR

	def convert_latex_to_mathml(self, latex: str) -> str:
		return self.latex_to_mathml(latex)

	def convert_mathml_to_xml(self, mathml: str) -> etree._ElementTree:
		return etree.fromstring(mathml)

	def convert_mathmlxml_to_omml(self, mathml: etree._ElementTree):
		return self.mathml_to_omml(mathml)

	def convert_omml_to_docx_element(self, omml: etree._ElementTree):
		return omml.getroot()


class Sanitiser:
	MATH_BEGIN = r'\begin{math}'
	MATH_END = r'\end{math}'
	MATH_CHECKER = r'$'

	@staticmethod
	def clean_mix_output(text: str) -> list[str]:
		sanitised = ['']
		in_math = False
		i = 0
		length = len(text)
		while i < length:
			if text[i] == Sanitiser.MATH_CHECKER:
				if in_math:
					sanitised[-1] += Sanitiser.MATH_END
					sanitised.append('')
				else:
					sanitised.append(r'\begin{math}')

				if text[min(i + 1, length)] == Sanitiser.MATH_CHECKER:
					i += 1

				in_math = not in_math

			else:
				sanitised[-1] += text[i]

			i += 1

		return sanitised


class P2TAnalyser:
	model = Pix2Text

	def __init__(self, languages = ('en',)):
		self.model = Pix2Text.from_config(languages=languages)

	def analyse(self, image: ImageType, type: Literal['text', 'formula', 'text_formula', 'page', 'pdf'] = 'text_formula'):
		result = self.model.recognize(image, file_type=type, return_text=True)
		return result


analyser = P2TAnalyser()
formatter = FormatConverter()


def analyse_p2t(image: ImageType, type: Literal['text', 'formula', 'text_formula', 'page', 'pdf'] = 'text_formula', output_type: Literal['latex', 'docx'] = 'latex') -> list[str] | BytesIO:
	results = analyser.analyse(image)

	match (type):
		case 'text_formula' | 'formula':
			results = Sanitiser.clean_mix_output(results)
		case 'text':
			results = [results]
		case _:
			raise NotImplementedError()

	match (output_type):
		case 'latex':
			return results

		case 'docx':
			document = Document()
			p = document.add_paragraph()

			for result in results:
				if result.startswith(Sanitiser.MATH_BEGIN):
					result = formatter.convert_latex_to_mathml(result)
					result = formatter.convert_mathml_to_xml(result)
					result = formatter.convert_mathmlxml_to_omml(result)
					result = formatter.convert_omml_to_docx_element(result)
					p._element.append(result)
				else:
					p.add_run(result)

			file_stream = BytesIO()
			document.save(file_stream)

			return file_stream


if __name__ == '__main__':
	image = Image.open(BASE_DIR / 'images' / 'sqrt-2.3.png')
	latex = analyse_p2t(image, 'text_formula', 'latex')
	stream = analyse_p2t(image, 'text_formula', 'docx')

	print(latex)

	filepath = 'pix2text.docx'
	with open(filepath, 'wb') as file:
		file.write(stream.getbuffer())
	print(f'File written at {filepath}')
