ENV_NAME = block_env

.PHONY: setup run clean clean-build deep-clean reset

setup:
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

run:
	@cd src && conda run --no-capture-output -n $(ENV_NAME) python -m main

clean:
	@echo "🧹 Cleaning workspace..."
	@rm -rf logs/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@if [ -d "data/" ]; then \
		printf "❓ Found data/ directory. Delete it? [y/N]: " && read ans; \
		if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
			rm -rf data/; \
			echo "🗑️  Data deleted."; \
		else \
			echo "📂 Keeping data directory."; \
		fi \
	fi
	@echo "✅ Cleanup complete."

clean-build:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf dist/ build/ output/ bloquinhos.spec
	@rm -f *.exe *.deb *.rpm
	@echo "✅ Build cleanup complete."

deep-clean: clean
	@echo "🚨 Performing deep clean..."
	@docker compose down -v --remove-orphans
	@rm -f .env
	@echo "✅ Deep cleanup complete."

reset: deep-clean setup
