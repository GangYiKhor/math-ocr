from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Literal

import latex2mathml.converter
import latex2mathml.exceptions
from docx import Document
from lxml import etree
from PIL.Image import Image as ImageType
from pix2text import Pix2Text

FILE_DIR = Path(__file__).resolve().parent
BASE_DIR = FILE_DIR.parent


class FormatConverter:
	def __init__(self):
		self.mathml_to_omml = etree.XSLT(etree.parse(BASE_DIR / 'data' / 'MML2OMML.XSL'))  # NOSONAR

	def latex_to_mathml(self, latex: str) -> str:
		mathml = latex2mathml.converter.convert(latex)
		mathml = mathml.replace(' display="inline"', '')
		return mathml

	def convert_latex_to_mathml(self, latex: str) -> str:
		return self.latex_to_mathml(latex)

	def convert_mathml_to_xml(self, mathml: str) -> etree._ElementTree:
		return etree.fromstring(mathml)

	def convert_mathmlxml_to_omml(self, mathml: etree._ElementTree) -> etree._ElementTree:
		return self.mathml_to_omml(mathml)

	def convert_omml_to_docx_element(self, omml: etree._ElementTree) -> etree._Element:
		return omml.getroot()

	def try_convert_latex_to_mathml(self, latex: str) -> str:
		try:
			return formatter.convert_latex_to_mathml(latex)
		except latex2mathml.exceptions.NoAvailableTokensError:
			return latex

	def try_convert_latex_to_omml(self, latex: str) -> str:
		try:
			output = formatter.convert_latex_to_mathml(latex)
			output = formatter.convert_mathml_to_xml(output)
			output = formatter.convert_mathmlxml_to_omml(output)
			return str(output)
		except latex2mathml.exceptions.NoAvailableTokensError:
			return latex


class Sanitiser:
	MATH_BEGIN = r'\begin{math}'
	MATH_END = r'\end{math}'
	MATRIX_BEGIN = r'\begin{matrix}'
	MATRIX_END = r'\end{matrix}'
	MATRIX_NEWLINE = r'\\'
	MATH_CHECKER = r'$'

	@staticmethod
	def parse_newline(sanitised: list[str], in_math: bool):
		if in_math:
			sanitised[-1] += Sanitiser.MATH_END
			sanitised.append(Sanitiser.MATH_BEGIN)
		else:
			sanitised.append('')

	@staticmethod
	def parse_math(sanitised: list[str], in_math: bool, next_char: str):
		"""Return `in_math`, `in_matrix`, `skip_index`"""

		if in_math:
			sanitised[-1] += Sanitiser.MATH_END
			sanitised.append('')
		else:
			sanitised.append(Sanitiser.MATH_BEGIN)

		# Skip the second $ (E.g. $$)
		if next_char == Sanitiser.MATH_CHECKER:
			return not in_math, False, 1
		else:
			return not in_math, False, 0

	@staticmethod
	def parse_matrix_newline(sanitised: list[str], in_math: bool):
		"""Return `skip`"""

		if in_math:
			sanitised[-1] += Sanitiser.MATH_END
			sanitised.append(Sanitiser.MATH_BEGIN)
			return 1

		return 0

	@staticmethod
	def parse_matrix_start(sanitised: list[str], in_math: bool, in_matrix: bool):
		"""Return `in_matrix`, `skip`"""

		if in_math and not in_matrix:
			sanitised[-1] += Sanitiser.MATH_END
			sanitised.append(Sanitiser.MATH_BEGIN)
			return True, len(Sanitiser.MATRIX_BEGIN) - 1

		return in_matrix, 0

	@staticmethod
	def parse_matrix_end(sanitised: list[str], in_math: bool, in_matrix: bool):
		"""Return `in_matrix`, `skip`"""

		if in_math and in_matrix:
			sanitised[-1] += Sanitiser.MATH_END
			sanitised.append(Sanitiser.MATH_BEGIN)
			return False, len(Sanitiser.MATRIX_END) - 1

		return in_matrix, 0

	@staticmethod
	def clean_mix_output(text: str) -> list[str]:
		sanitised = ['']
		in_math = False
		in_matrix = False
		i = 0
		length = len(text)

		while i < length:
			char1 = text[i]
			char2 = text[i + 1] if i + 1 < length else ''

			if char1 == '\n':
				Sanitiser.parse_newline(sanitised, in_math)

			elif char1 == Sanitiser.MATH_CHECKER:
				in_math, in_matrix, skip = Sanitiser.parse_math(sanitised, in_math, char2)
				i += skip

			elif char1 + char2 == Sanitiser.MATRIX_NEWLINE:
				i += Sanitiser.parse_matrix_newline(sanitised, in_math)

			elif text[i:].startswith(Sanitiser.MATRIX_BEGIN):
				in_matrix, skip = Sanitiser.parse_matrix_start(sanitised, in_math, in_matrix)
				i += skip

			elif text[i:].startswith(Sanitiser.MATRIX_END):
				in_matrix, skip = Sanitiser.parse_matrix_end(sanitised, in_math, in_matrix)
				i += skip

			else:
				sanitised[-1] += char1

			i += 1

		sanitised = filter(lambda x: x not in ['', '\n', f'{Sanitiser.MATH_BEGIN}{Sanitiser.MATH_END}'], sanitised)
		sanitised = list(sanitised)
		return sanitised


class P2TAnalyser:
	model = Pix2Text

	def __init__(self, languages=('en',)):
		self.model = Pix2Text.from_config(languages=languages)

	def analyse(
		self,
		image: ImageType,
		type: Literal['text', 'formula', 'text_formula', 'page', 'pdf'] = 'text_formula',
	):
		result = self.model.recognize(image, file_type=type)
		return result


class P2TInput(Enum):
	TEXT = 'text'
	FORMULA = 'formula'
	TEXT_FORMULA = 'text_formula'
	PAGE = 'page'
	PDF = 'pdf'


class P2TOutput(Enum):
	LATEX = 'latex'
	MATHML = 'mathml'
	OMML = 'omml'
	DOCX = 'docx'


analyser = P2TAnalyser()
formatter = FormatConverter()


def convert_output(results: list[str], output_type: P2TOutput) -> list[str] | BytesIO:
	match output_type:
		case P2TOutput.LATEX:
			return results

		case P2TOutput.MATHML:
			return [formatter.try_convert_latex_to_mathml(result) for result in results]

		case P2TOutput.OMML:
			return [
				formatter.try_convert_latex_to_omml(result)
				for result in results
				if result.startswith(Sanitiser.MATH_BEGIN)
			]

		case P2TOutput.DOCX:
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


def analyse_p2t(
	image: ImageType | Path,
	input_type: P2TInput = P2TInput.TEXT_FORMULA,
	output_type: P2TOutput | list[P2TOutput] = P2TOutput.LATEX,
) -> list[str] | BytesIO | dict[str, list[str] | BytesIO]:
	results = analyser.analyse(image, input_type.value)

	match input_type.value:
		case P2TInput.TEXT_FORMULA.value | P2TInput.FORMULA.value:
			results = Sanitiser.clean_mix_output(results)
		case P2TInput.TEXT.value:
			results = [results]
		case P2TInput.PDF.value:
			results.to_markdown('output-pdf-md')
		case _:
			raise NotImplementedError('Input Not Implemented!')

	if isinstance(output_type, list):
		outputs = {out_type.value: convert_output(results, out_type) for out_type in output_type}
		return outputs

	return convert_output(results, output_type)
