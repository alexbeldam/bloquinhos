ENV_NAME = $(shell bash scripts/get-meta.sh env_name)
PYINSTALLER ?= pyinstaller
VERSION ?= $(shell bash scripts/get-meta.sh version)
APP_ID ?= $(shell bash scripts/get-meta.sh app_id)
APP_DISPLAY ?= $(shell bash scripts/get-meta.sh app_display)
MAINTAINER ?= $(shell bash scripts/get-meta.sh maintainer_line)
VENDOR ?= $(shell bash scripts/get-meta.sh vendor)
LINUX_DEB_ARCH ?= $(shell bash scripts/get-meta.sh deb_arch)
LINUX_RPM_ARCH ?= $(shell bash scripts/get-meta.sh rpm_arch)
WINDOWS_ARCH ?= $(shell bash scripts/get-meta.sh windows_arch)
APP_SETUP_BASENAME ?= $(APP_DISPLAY)Setup
RPM_BASE_VERSION ?= $(shell bash scripts/get-meta.sh rpm_base_version)
RPM_PKG_RELEASE ?= $(shell bash scripts/get-meta.sh rpm_pkg_release)
DEB_PKG_RELEASE ?= $(shell bash scripts/get-meta.sh deb_pkg_release)
WIN_NUMERIC_VERSION ?= $(shell bash scripts/get-meta.sh win_numeric_version)

.PHONY: help setup env-sync docker-build start stop run run-dev update \
	clean clean-cache clean-coverage clean-logs clean-data \
	clean-build clean-package clean-docker clean-env clean-conda \
	deep-clean reset \
	build-linux build-windows package-linux-deps package-deb package-rpm package-linux package-windows \
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
	@echo "  make package-deb      - Package DEB installer (Linux only)"
	@echo "  make package-rpm      - Package RPM installer (Linux only)"
	@echo "  make package-linux    - Package both DEB and RPM (Linux only)"

setup:
	@bash scripts/setup.sh

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
	@if [ -z "$(APP_ID)" ]; then echo "❌ Could not resolve APP_ID from pyproject.toml."; exit 1; fi
	@command -v $(PYINSTALLER) >/dev/null 2>&1 || { echo "❌ PyInstaller not found. Install it first or set PYINSTALLER."; exit 1; }
	@echo "🔧 Building Linux executable..."
	@$(PYINSTALLER) --onedir --windowed --name "$(APP_ID)" --paths src --add-data ".env:." src/main.py
	@echo "✅ Linux build complete."

build-windows:
	@if [ -z "$(APP_ID)" ]; then echo "❌ Could not resolve APP_ID from pyproject.toml."; exit 1; fi
	@command -v $(PYINSTALLER) >/dev/null 2>&1 || { echo "❌ PyInstaller not found. Install it first or set PYINSTALLER."; exit 1; }
	@echo "🔧 Building Windows executable..."
	@$(PYINSTALLER) --onedir --windowed --name "$(APP_ID)" --paths src --icon="assets/img/icon.ico" --add-data ".env;." src/main.py
	@echo "✅ Windows build complete."

package-linux-deps:
	@if [ -z "$(VERSION)" ]; then echo "❌ Could not resolve VERSION from pyproject.toml."; exit 1; fi
	@if [ -z "$(APP_ID)" ]; then echo "❌ Could not resolve APP_ID from pyproject.toml."; exit 1; fi
	@if [ -z "$(MAINTAINER)" ]; then echo "❌ Could not resolve MAINTAINER from pyproject.toml."; exit 1; fi
	@if [ -z "$(VENDOR)" ]; then echo "❌ Could not resolve VENDOR from pyproject.toml."; exit 1; fi
	@command -v nfpm >/dev/null 2>&1 || { echo "❌ nFPM not found. Install it first."; exit 1; }
	@command -v envsubst >/dev/null 2>&1 || { echo "❌ envsubst not found. Install gettext package."; exit 1; }

package-deb: package-linux-deps
	@if [ -z "$(LINUX_DEB_ARCH)" ]; then echo "❌ Could not resolve LINUX_DEB_ARCH from pyproject.toml."; exit 1; fi
	@if [ -z "$(APP_DISPLAY)" ]; then echo "❌ Could not resolve APP_DISPLAY from pyproject.toml."; exit 1; fi
	@if [ -z "$(DEB_PKG_RELEASE)" ]; then echo "❌ Could not resolve DEB_PKG_RELEASE from pyproject.toml."; exit 1; fi
	@echo "📦 Packaging DEB (version $(VERSION))..."
	@APP_ID="$(APP_ID)" APP_DISPLAY="$(APP_DISPLAY)" VERSION="$(VERSION)" PKG_RELEASE="$(DEB_PKG_RELEASE)" MAINTAINER="$(MAINTAINER)" VENDOR="$(VENDOR)" PACKAGE_ARCH="$(LINUX_DEB_ARCH)" envsubst < nfpm.yaml > nfpm.yaml.tmp
	@nfpm pkg --config nfpm.yaml.tmp --packager deb --target $(APP_ID)_$(VERSION)_$(LINUX_DEB_ARCH).deb
	@rm nfpm.yaml.tmp
	@echo "✅ DEB packaging complete."

package-rpm: package-linux-deps
	@if [ -z "$(LINUX_RPM_ARCH)" ]; then echo "❌ Could not resolve LINUX_RPM_ARCH from pyproject.toml."; exit 1; fi
	@if [ -z "$(APP_DISPLAY)" ]; then echo "❌ Could not resolve APP_DISPLAY from pyproject.toml."; exit 1; fi
	@if [ -z "$(RPM_BASE_VERSION)" ]; then echo "❌ Could not resolve RPM_BASE_VERSION from pyproject.toml."; exit 1; fi
	@if [ -z "$(RPM_PKG_RELEASE)" ]; then echo "❌ Could not resolve RPM_PKG_RELEASE from pyproject.toml."; exit 1; fi
	@echo "📦 Packaging RPM (version $(VERSION))..."
	@APP_ID="$(APP_ID)" APP_DISPLAY="$(APP_DISPLAY)" VERSION="$(RPM_BASE_VERSION)" PKG_RELEASE="$(RPM_PKG_RELEASE)" MAINTAINER="$(MAINTAINER)" VENDOR="$(VENDOR)" PACKAGE_ARCH="$(LINUX_RPM_ARCH)" envsubst < nfpm.yaml > nfpm.yaml.tmp
	@nfpm pkg --config nfpm.yaml.tmp --packager rpm --target $(APP_ID)-$(RPM_BASE_VERSION)-$(RPM_PKG_RELEASE).$(LINUX_RPM_ARCH).rpm
	@rm nfpm.yaml.tmp
	@echo "✅ RPM packaging complete."

package-linux: package-deb package-rpm
	
package-windows:
	@if [ -z "$(VERSION)" ]; then echo "❌ Could not resolve VERSION from pyproject.toml."; exit 1; fi
	@if [ -z "$(APP_ID)" ]; then echo "❌ Could not resolve APP_ID from pyproject.toml."; exit 1; fi
	@if [ -z "$(APP_DISPLAY)" ]; then echo "❌ Could not resolve APP_DISPLAY from pyproject.toml."; exit 1; fi
	@if [ -z "$(WINDOWS_ARCH)" ]; then echo "❌ Could not resolve WINDOWS_ARCH from pyproject.toml."; exit 1; fi
	@if [ -z "$(APP_SETUP_BASENAME)" ]; then echo "❌ Could not resolve APP_SETUP_BASENAME."; exit 1; fi
	@if [ -z "$(WIN_NUMERIC_VERSION)" ]; then echo "❌ Could not resolve WIN_NUMERIC_VERSION from pyproject.toml."; exit 1; fi
	@command -v iscc.exe >/dev/null 2>&1 || { echo "❌ Inno Setup Compiler (iscc.exe) not found."; exit 1; }
	@echo "📦 Packaging Windows installer (version $(VERSION))..."
	@iscc.exe /DMyAppVersion=$(VERSION) /DMyVersionInfoVersion=$(WIN_NUMERIC_VERSION) /DMyAppId=$(APP_ID) /DMyAppName=$(APP_DISPLAY) /DMyAppExe=$(APP_ID).exe /DMyOutputBaseFilename=$(APP_SETUP_BASENAME) scripts/install_script.iss
	@mv output/$(APP_SETUP_BASENAME).exe $(APP_SETUP_BASENAME)_v$(VERSION)_$(WINDOWS_ARCH).exe
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