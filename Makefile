build:
	npm --prefix ./frontend run build

run/prod:
	$(MAKE) build & $(MAKE) runserver

runserver:
	python startserver.py
