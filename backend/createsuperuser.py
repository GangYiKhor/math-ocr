import re
import sys
from pathlib import Path

import bcrypt
from colorama import Fore, Style
from sqlmodel import Session

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.createuser import account_input
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

	invalid_characters = re.findall(f'[^{number_re}{lower_re}{upper_re}{symbol_re}]', password)
	if invalid_characters:
		error.append(f'Invalid symbol! "{'", "'.join(list(set(invalid_characters)))}"')

	if len(error) > 0:
		raise ValueError('\n'.join(error))


def main():
	try:
		create_db_and_tables()

		with Session(engine) as db_session:
			full_name, username, password = account_input(db_session)

			password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
			user = User(username=username, full_name=full_name, password=password, is_activated=True, admin=True)
			create_user(user, db_session)

			print(Fore.GREEN + 'User Created!' + Style.RESET_ALL)
	except KeyboardInterrupt:
		print(Fore.RED + '\nUser creation cancelled!' + Style.RESET_ALL)


if __name__ == '__main__':
	main()
