ENV_NAME = tetris_env

.PHONY: setup run

setup:
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

run:
	@conda run --no-capture-output -n $(ENV_NAME) python src/main.py