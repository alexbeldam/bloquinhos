.PHONY: setup run

setup:
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

run:
	@source .venv/bin/activate && python src/main.py
