import math
import re


class Sanitiser:
	ARRAY_BEGIN = r'\begin{array}'
	ARRAY_END = r'\end{array}'
	MATH_BEGIN = r'\begin{math}'
	MATH_END = r'\end{math}'
	MATRIX_BEGIN = r'\begin{matrix}'
	MATRIX_END = r'\end{matrix}'
	MATRIX_NEWLINE = r'\\'
	MATH_CHECKER = r'$'
	SYNTAX = {
		'{': '}',
		r'\left': r'\right',
	}
	UNCLOSED_REPLACE = {
		r'\right': r'\right.',
	}
	EMPTY = [
		'',
		'\n',
		f'{MATH_BEGIN}{MATH_END}',
		f'{MATH_BEGIN} {MATH_END}',
	]
	UNRECOGNISED = [
		r'\textcircled',
	]

	def assign_math(self, text: str) -> str:
		math = [self.MATH_BEGIN, self.MATH_END]
		math_open = 0
		while self.MATH_CHECKER in text:
			text = re.sub(rf'\{self.MATH_CHECKER}+', rf'\{math[math_open]}', text, 1)
			math_open ^= 1
		return text

	def split(self, text: str) -> list[str]:
		splitted = text.split(self.MATH_END)
		for i in range(len(splitted) - 1):
			splitted[i] += self.MATH_END

		splitted = [split.split(self.MATH_BEGIN) for split in splitted if split != '']
		for i in range(len(splitted)):
			for j in range(1, len(splitted[i])):
				splitted[i][j] = self.MATH_BEGIN + splitted[i][j]

		splitted = [x for split in splitted for x in split]
		splitted = filter(lambda x: x not in self.EMPTY, splitted)
		return list(splitted)

	def fix_syntax(self, text: str) -> str:
		cleaned_text = ''
		syntax_stack = []

		i = 0
		line_length = len(text)
		while i < line_length:
			sliced = text[i:]

			# Correct closer syntax
			if len(syntax_stack) > 0 and sliced.startswith(syntax_stack[-1]):
				add = syntax_stack.pop()
				cleaned_text += add
				i += len(add)
				continue

			# Have unclosed syntax, also close them first
			is_closer = False
			temp_stack = []
			for j in range(len(syntax_stack) - 1, -1, -1):
				temp_stack.append(syntax_stack[j])
				if sliced.startswith(syntax_stack[j]):
					is_closer = True
					break

			if is_closer:
				for k in range(len(temp_stack) - 1):
					if temp_stack[k] in self.UNCLOSED_REPLACE:
						temp_stack[k] = self.UNCLOSED_REPLACE[temp_stack[k]]

				cleaned_text += ' '.join(temp_stack)
				i += len(temp_stack[-1])
				syntax_stack = syntax_stack[0:j]
				continue

			# Closer syntax without opener, skip it
			is_closer = False
			for closer in self.SYNTAX.values():
				if sliced.startswith(closer):
					is_closer = True
					i += len(closer)
					break

			if is_closer:
				continue

			# Record syntax into stack
			is_syntax = False
			for opener, closer in self.SYNTAX.items():
				if sliced.startswith(opener):
					cleaned_text += opener
					syntax_stack.append(closer)
					is_syntax = True
					i += len(opener)
					break

			if is_syntax:
				continue

			# If not syntax, find location of the next syntax
			next_index = math.inf
			for opener, closer in self.SYNTAX.items():
				for search_text in [opener, closer]:
					matched = re.search(rf'[^\\]{search_text.replace("\\", r"\\")}', sliced)
					if matched is not None:
						next_index = min(matched.start() + 1, next_index)

			cleaned_text += sliced[0:next_index]
			i += next_index

		# Close all unclosed syntax
		for unclosed in syntax_stack[::-1]:
			unclosed = self.UNCLOSED_REPLACE.get(unclosed, unclosed)
			cleaned_text = cleaned_text.replace(self.MATH_END, f'{unclosed} {self.MATH_END}')

		# Remove unrecognised syntax
		for unrecognised in self.UNRECOGNISED:
			cleaned_text = cleaned_text.replace(unrecognised, '')

		return cleaned_text

	def process_line(self, line: str) -> list[str]:
		if self.MATH_BEGIN not in line:
			return line.splitlines()

		lines = [
			re.sub(rf'(\{self.MATRIX_BEGIN}|\{self.MATRIX_END})', '', text)
			for row in line.splitlines()
			for text in row.split(self.MATRIX_NEWLINE)
		]

		for i in range(len(lines)):
			if not lines[i].startswith(self.MATH_BEGIN):
				lines[i] = self.MATH_BEGIN + lines[i]
			if not lines[i].endswith(self.MATH_END):
				lines[i] += self.MATH_END

			if self.ARRAY_BEGIN in lines[i] and self.ARRAY_END not in lines[i]:
				lines[i] = lines[i].replace(self.ARRAY_BEGIN, '')
			if self.ARRAY_END in lines[i] and self.ARRAY_BEGIN not in lines[i]:
				lines[i] = lines[i].replace(self.ARRAY_END, '')
			if self.ARRAY_BEGIN not in lines[i]:
				lines[i] = re.sub(r'([^\\])&', r'\1', lines[i])

		lines = [self.fix_syntax(line) for line in lines]
		return lines

	def clean_mix_output(self, text: str) -> list[str]:
		text = self.assign_math(text)
		sanitised = [
			text  #
			for line in self.split(text)
			for text in self.process_line(line)
		]

		sanitised = filter(lambda x: x not in self.EMPTY, sanitised)
		return list(sanitised)
