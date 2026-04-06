ENV_NAME = block_env

.PHONY: setup run clean reset

setup:
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

run:
	@cd src && conda run --no-capture-output -n $(ENV_NAME) python -m main

clean:
	@echo "🧹 Cleaning infrastructure and artifacts..."
	@docker compose down -v --remove-orphans
	@rm -f .env
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✅ Cleanup complete."

reset: clean setup
