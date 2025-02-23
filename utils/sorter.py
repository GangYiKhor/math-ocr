from functools import cmp_to_key
from pathlib import Path
import re

class Sorter:
	@cmp_to_key
	@staticmethod
	def compare_path(parts_1: list[str], parts_2: list[str]) -> int:
		parts_1 = parts_1[1]
		parts_2 = parts_2[1]
		len_1 = len(parts_1)
		len_2 = len(parts_2)

		for i in range(min(len_1, len_2)):
			is_float_1 = isinstance(parts_1[i], float)
			is_float_2 = isinstance(parts_2[i], float)

			if is_float_1 and is_float_2:
				# If same number, check next part
				if parts_1[i] == parts_2[i]:
					continue

				# If not same, just compare that
				else:
					return parts_1[i] - parts_2[i]

			# If only one is numeric, numeric first
			elif is_float_1:
				return -1
			elif is_float_2:
				return 1

			# Else compare string if not same
			elif parts_1[i] != parts_2[i]:
				return 1 if parts_1[i] > parts_2[i] else -1

		return len_2 - len_1

	@staticmethod
	def sort_paths(paths: list[Path]) -> list[Path]:
		stems = []

		for path in paths:
			stem = path.stem
			parts = re.findall(r'(\d+\.\d+|\d+|[^\d+]+)', stem)

			for i in range(len(parts)):
				try:
					parts[i] = float(parts[i])
				except ValueError:
					pass

			stems.append([path, parts])

		stems = [stem[0] for stem in sorted(stems, key=Sorter.compare_path)]
		return stems
