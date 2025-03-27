build:
	npm --prefix ./frontend run build

run/prod:
	npm --prefix ./frontend run build && fastapi run backend/main.py
