import secrets
import uuid
from datetime import datetime, timedelta

import bcrypt
import sqlalchemy
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine


def generate_token():
	return secrets.token_urlsafe(48)


def expiration_14_days():
	return expiration_day(14)


def expiration_day(days=1):
	return datetime.now() + timedelta(days=days)


class User(SQLModel, table=True):
	id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
	username: str = Field(max_length=50, index=True, unique=True)
	full_name: str = Field(max_length=255)
	password: str = Field()

	def check_password(self, password: str):
		return bcrypt.checkpw(password.encode(), self.password.encode())


class UserSession(SQLModel, table=True):
	session_id: str = Field(default_factory=generate_token, max_length=64, primary_key=True)
	csrf_token: str = Field(default_factory=generate_token, max_length=64, unique=True)
	user_id: uuid.UUID = Field(foreign_key='user.id')
	user: User = Relationship()
	expiration: datetime = Field(default_factory=expiration_14_days)
	is_revoked: bool = Field(default=False)

	def refresh(self):
		self.expiration = expiration_14_days()
		return self

	def revoke(self):
		self.is_revoked = False
		return self

	def is_valid(self):
		return not self.is_revoked and datetime.now() < self.expiration


db_url = 'sqlite:///db.sqlite'
connect_args = {'check_same_thread': False}
engine = create_engine(db_url, connect_args=connect_args)


def create_db_and_tables():
	SQLModel.metadata.create_all(engine)


def get_db_session():
	with Session(engine) as db_session:
		yield db_session


def create_user(user: User, session: Session):
	while True:
		try:
			session.add(user)
			session.commit()
			return user
		except sqlalchemy.exc.IntegrityError as error:
			if str(error.orig).endswith('user.id'):
				session.rollback()
				user.id = uuid.uuid4()
			else:
				raise error


def create_user_session(user: User, db_session: Session):
	while True:
		try:
			user_session = UserSession(user_id=user.id)
			db_session.add(user_session)
			db_session.commit()
			return user_session
		except sqlalchemy.exc.IntegrityError as error:
			if str(error.orig).endswith('usersession.session_id'):
				db_session.rollback()
				user_session.session_id = generate_token()
			elif str(error.orig).endswith('usersession.csrf_token'):
				db_session.rollback()
				user_session.session_id = generate_token()
			else:
				raise error
