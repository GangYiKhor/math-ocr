import sys
from pathlib import Path

from colorama import Fore, Style
from sqlmodel import Session, select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.models import User, create_db_and_tables, engine


def main():
	try:
		create_db_and_tables()

		with Session(engine) as db_session:
			while True:
				inactivated_users = select(User).where(User.is_activated == False)  # noqa: E712
				inactivated_users = db_session.exec(inactivated_users).all()

				if len(inactivated_users) == 0:
					print(Fore.GREEN + 'No pending account to activate!' + Style.RESET_ALL)
					return

				i = 1
				print(Fore.YELLOW + 'Pending users:' + Style.RESET_ALL)
				for user in inactivated_users:
					print(f'{i}: {user.username} ({user.full_name})')
					i += 1

				activate_index = input(
					f'Which user do you want to activate? ({Fore.RED}-1 to exit{Style.RESET_ALL}, {Fore.GREEN}0 to activate all{Style.RESET_ALL})\n'
				)

				try:
					activate_index = int(activate_index)
				except ValueError:
					print(Fore.RED + 'Invalid number' + Style.RESET_ALL)

				match activate_index:
					case -1:
						return

					case 0:
						for user in inactivated_users:
							user.is_activated = True
							db_session.add(user)
						print(Fore.GREEN + 'All accounts activated!' + Style.RESET_ALL)

					case _:
						inactivated_users[activate_index - 1].is_activated = True
						db_session.add(inactivated_users[activate_index - 1])
						print(
							Fore.GREEN
							+ f'{inactivated_users[activate_index - 1].username} activated!'
							+ Style.RESET_ALL
						)

				db_session.commit()

				if activate_index == 0:
					return
	except KeyboardInterrupt:
		print(Fore.RED + 'Cancelled!' + Style.RESET_ALL)


if __name__ == '__main__':
	main()
