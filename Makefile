ENV_NAME = $(shell scripts/get-env-name)
PYINSTALLER ?= pyinstaller
VERSION ?= $(shell scripts/get-version)

.PHONY: help setup env-sync docker-build start stop run run-dev update \
	clean clean-cache clean-coverage clean-logs clean-data \
	clean-build clean-package clean-docker clean-env clean-conda \
	deep-clean reset \
	build-linux build-windows package-linux package-windows \
	build package

help:
	@echo "Available targets:"
	@echo "  make setup            - Create/update Conda env and start Docker services"
	@echo "  make env-sync         - Create or update Conda environment"
	@echo "  make docker-build     - Rebuild local Docker images"
	@echo "  make start            - Start local Docker services"
	@echo "  make stop             - Stop local Docker services"
	@echo "  make run              - Run the game"
	@echo "  make run-dev          - Start local Docker services and run the game"
	@echo "  make update           - Update Conda dependencies from environment.yml"
	@echo "  make clean            - Clean cache, coverage, and logs"
	@echo "  make clean-build      - Clean build artifacts"
	@echo "  make clean-package    - Clean packaged installers (.exe/.deb/.rpm)"
	@echo "  make clean-data       - Remove local data directory"
	@echo "  make clean-docker     - Stop/remove Docker containers and volumes"
	@echo "  make clean-env        - Remove .env file"
	@echo "  make clean-conda      - Remove Conda environment"
	@echo "  make deep-clean       - Full cleanup (workspace, build, data, Docker, env, Conda)"
	@echo "  make reset            - Deep clean then setup"
	@echo "  make build            - Build executable for current OS"
	@echo "  make package          - Package artifacts for current OS"

setup:
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

env-sync:
	@if conda info --envs | grep -q "^$(ENV_NAME)[[:space:]]"; then \
		echo "⚠️ Conda environment '$(ENV_NAME)' already exists. Updating dependencies..."; \
		$(MAKE) --no-print-directory update; \
	else \
		echo "📦 Creating Conda environment ($(ENV_NAME))..."; \
		conda env create -f environment.yml; \
		echo "✅ Conda environment created."; \
	fi

docker-build:
	@echo "🏗️ Building local Docker images..."
	@docker compose build
	@echo "✅ Local Docker images built."

start:
	@echo "🐳 Starting local Docker services..."
	@docker compose up -d
	@echo "✅ Local Docker services started."

stop:
	@echo "🛑 Stopping local Docker services..."
	@docker compose stop
	@echo "✅ Local Docker services stopped."

run:
	@clear
	@cd src && conda run --no-capture-output -n $(ENV_NAME) python -m main

run-dev: start run

update:
	@echo "📦 Updating Conda dependencies for $(ENV_NAME)..."
	@conda env update -n $(ENV_NAME) -f environment.yml --prune
	@echo "✅ Conda dependencies updated."

clean: clean-cache clean-coverage clean-logs
	@echo "✅ Workspace cleanup complete."

clean-cache:
	@echo "🧹 Cleaning Python and tool caches..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -rf .pytest_cache/ .mypy_cache/ htmlcov/
	@echo "✅ Cache cleanup complete."

clean-coverage:
	@echo "🧹 Cleaning coverage files..."
	@rm -f .coverage
	@echo "✅ Coverage cleanup complete."

clean-logs:
	@echo "🧹 Cleaning logs..."
	@rm -rf logs/
	@rm -f *.log
	@echo "✅ Log cleanup complete."

clean-data:
	@echo "🧹 Cleaning local data directory..."
	@rm -rf data/
	@echo "✅ Data cleanup complete."

clean-build:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf *.egg-info src/*.egg-info .eggs/
	@rm -rf dist/ build/ output/ *.spec
	@echo "✅ Build cleanup complete."

clean-package:
	@echo "🧹 Cleaning installer packages..."
	@rm -f *.exe *.deb *.rpm
	@echo "✅ Installer cleanup complete."

clean-docker:
	@echo "🧹 Cleaning Docker resources..."
	@docker compose down -v --remove-orphans
	@echo "✅ Docker cleanup complete."

clean-env:
	@echo "🧹 Cleaning environment files..."
	@rm -f .env
	@echo "✅ Environment cleanup complete."

clean-conda:
	@echo "🧹 Cleaning Conda environment ($(ENV_NAME))..."
	@if conda info --envs | grep -q "^$(ENV_NAME)[[:space:]]"; then \
		conda env remove -n $(ENV_NAME) -y; \
		echo "✅ Conda environment removed."; \
	else \
		echo "ℹ️ Conda environment not found. Skipping."; \
	fi

deep-clean: clean clean-build clean-package clean-data clean-docker clean-env clean-conda
	@echo "🚨 Performing deep clean..."
	@echo "✅ Deep cleanup complete."

reset: deep-clean setup

build-linux:
	@command -v $(PYINSTALLER) >/dev/null 2>&1 || { echo "❌ PyInstaller not found. Install it first or set PYINSTALLER."; exit 1; }
	@echo "🔧 Building Linux executable..."
	@$(PYINSTALLER) --onedir --windowed --name "bloquinhos" --paths src --add-data ".env:." src/main.py
	@echo "✅ Linux build complete."

build-windows:
	@command -v $(PYINSTALLER) >/dev/null 2>&1 || { echo "❌ PyInstaller not found. Install it first or set PYINSTALLER."; exit 1; }
	@echo "🔧 Building Windows executable..."
	@$(PYINSTALLER) --onedir --windowed --name "bloquinhos" --paths src --icon="assets/img/icon.ico" --add-data ".env;." src/main.py
	@echo "✅ Windows build complete."

package-linux:
	@if [ -z "$(VERSION)" ]; then echo "❌ Could not resolve VERSION from pyproject.toml."; exit 1; fi
	@command -v nfpm >/dev/null 2>&1 || { echo "❌ nFPM not found. Install it first."; exit 1; }
	@echo "📦 Packaging Linux DEB and RPM (version $(VERSION))..."
	@nfpm pkg --packager deb --target bloquinhos_$(VERSION)_amd64.deb
	@nfpm pkg --packager rpm --target bloquinhos-$(VERSION)-x86_64.rpm
	@echo "✅ Linux packaging complete."
	
package-windows:
	@if [ -z "$(VERSION)" ]; then echo "❌ Could not resolve VERSION from pyproject.toml."; exit 1; fi
	@command -v iscc.exe >/dev/null 2>&1 || { echo "❌ Inno Setup Compiler (iscc.exe) not found."; exit 1; }
	@echo "📦 Packaging Windows installer (version $(VERSION))..."
	@iscc.exe /DMyAppVersion=$(VERSION) scripts/install_script.iss
	@mv output/BloquinhosSetup.exe BloquinhosSetup_v$(VERSION)_x64.exe
	@echo "✅ Windows packaging complete."

build:
ifeq ($(OS),Windows_NT)
	@$(MAKE) build-windows
else
	@$(MAKE) build-linux
endif

package:
ifeq ($(OS),Windows_NT)
	@$(MAKE) package-windows VERSION=$(VERSION)
else
	@$(MAKE) package-linux VERSION=$(VERSION)
endif

.DEFAULT:
	@echo "Unknown target: $(MAKECMDGOALS)"
	@$(MAKE) --no-print-directory help
	@exit 2