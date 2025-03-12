import re
import sys
from getpass import getpass
from pathlib import Path

import bcrypt
from colorama import Fore, Style
from sqlmodel import Session, select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.models import User, create_db_and_tables, create_user, engine

number_re = '0-9'
lower_re = 'a-z'
upper_re = 'A-Z'
symbol_re = '`~!@#$%^&*()\\-=_+[\\]{}\\\\|;\':",./<>?\\s'
min_length = 8
max_length = 24
min_user_length = 4
max_user_length = 24


def check_password(password: str):
	error = []

	if not min_length <= len(password) <= max_length:
		error.append(f'Password must be {min_length}-{max_length} characters!')

	if not re.search(f'[{number_re}]', password):
		error.append('Password must contain numbers!')

	if not re.search(f'[{lower_re}]', password):
		error.append('Password must contain lowercase alphabets!')

	if not re.search(f'[{upper_re}]', password):
		error.append('Password must contain uppercase alphabets!')

	if not re.search(f'[{symbol_re}]', password):
		error.append('Password must contain symbols!')

	invalid_characters = re.findall(f'[^{number_re}{lower_re}{upper_re}{symbol_re}]', password)
	if invalid_characters:
		error.append(f'Invalid symbol! "{'", "'.join(list(set(invalid_characters)))}"')

	if len(error) > 0:
		raise ValueError('\n'.join(error))


def main():
	try:
		create_db_and_tables()

		with Session(engine) as db_session:
			full_name = input('Please enter your full name: ')

			while True:
				username = input('Please enter your username: ')

				if not min_user_length <= len(username) <= max_user_length:
					print(
						Fore.RED
						+ f'Username must be more than {min_user_length}-{max_user_length} characters'
						+ Style.RESET_ALL
					)
					continue

				existing_user = select(User).where(User.username == username)
				existing_user = db_session.exec(existing_user).first()

				if existing_user is not None:
					print(Fore.RED + 'Username taken!' + Style.RESET_ALL)
				else:
					break

			while True:
				try:
					password = getpass('Please enter your password: ')
					check_password(password)
					break
				except ValueError as error:
					print(Fore.RED + str(error) + Style.RESET_ALL)

			while True:
				if getpass('Please re-enter your password (Ctrl + C to cancel): ') != password:
					print(Fore.RED + 'Password not matched!' + Style.RESET_ALL)
				else:
					break

			password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
			user = User(username=username, full_name=full_name, password=password)
			create_user(user, db_session)

			print(Fore.GREEN + 'User Created!' + Style.RESET_ALL)
	except KeyboardInterrupt:
		print(Fore.RED + '\nUser creation cancelled!' + Style.RESET_ALL)


if __name__ == '__main__':
	main()
