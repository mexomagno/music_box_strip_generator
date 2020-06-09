THIS_FILE := $(lastword $(MAKEFILE_LIST))

# target: all - Default target. Does nothing.
all:
	@echo "Hello $(LOGNAME), nothing to do by default.";
	@echo "Try 'make help'.";

# target: dev - Builds the project using 'development' settings.
dev:
	pip install lib/python3-midi
	pip install -r requirements/dev.txt;

prod:
	pip install lib/python3-midi
	pip install -r requirements/base.txt;

