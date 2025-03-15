import sys
from getpass import getpass
from pathlib import Path

import bcrypt
from colorama import Fore, Style
from sqlmodel import Session, select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.createuser import check_password
from backend.models import User, create_db_and_tables, engine


def main():
	try:
		create_db_and_tables()

		with Session(engine) as db_session:
			username = input('Please enter your username: ')
			user = select(User).where(User.username == username)
			user = db_session.exec(user).first()

			if user is None:
				print(Fore.RED + 'User not found!' + Style.RESET_ALL)
				return

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
			user.password = password
			db_session.add(user)
			db_session.commit()

			print(Fore.GREEN + 'Password changed!' + Style.RESET_ALL)
	except KeyboardInterrupt:
		print(Fore.RED + 'Cancelled!' + Style.RESET_ALL)


if __name__ == '__main__':
	main()
