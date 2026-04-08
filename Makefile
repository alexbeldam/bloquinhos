ENV_NAME = block_env

.PHONY: setup run clean clean-build deep-clean reset \
        build-linux build-windows package-linux package-windows \
        build package

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

build-linux:
	@command -v pyinstaller >/dev/null 2>&1 || { echo "❌ PyInstaller not found. Install it first."; exit 1; }
	@echo "🔧 Building Linux executable..."
	@pyinstaller --onedir --windowed --name "bloquinhos" --paths src --add-data ".env:." src/main.py
	@echo "✅ Linux build complete."

build-windows:
	@command -v pyinstaller >/dev/null 2>&1 || { echo "❌ PyInstaller not found. Install it first."; exit 1; }
	@echo "🔧 Building Windows executable..."
	@pyinstaller --onedir --windowed --name "bloquinhos" --paths src --icon="assets/img/icon.ico" --add-data ".env;." src/main.py
	@echo "✅ Windows build complete."

package-linux:
ifndef VERSION
	$(error ❌ VERSION must be specified, e.g., make package-linux VERSION=1.2.3)
endif
	@command -v nfpm >/dev/null 2>&1 || { echo "❌ nFPM not found. Install it first."; exit 1; }
	@echo "📦 Packaging Linux DEB and RPM (version $(VERSION))..."
	@nfpm pkg --packager deb --target bloquinhos_$(VERSION)_amd64.deb
	@nfpm pkg --packager rpm --target bloquinhos-$(VERSION)-x86_64.rpm
	@echo "✅ Linux packaging complete."
	
package-windows:
ifndef VERSION
	$(error ❌ VERSION must be specified, e.g., make package-windows VERSION=1.2.3)
endif
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
ifndef VERSION
	$(error ❌ VERSION must be specified, e.g., make package VERSION=1.2.3)
endif
	@$(MAKE) package-windows VERSION=$(VERSION)
else
ifndef VERSION
	$(error ❌ VERSION must be specified, e.g., make package VERSION=1.2.3)
endif
	@$(MAKE) package-linux VERSION=$(VERSION)
endif