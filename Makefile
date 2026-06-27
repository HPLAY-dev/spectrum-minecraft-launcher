# MC Launcher — build shortcuts
# Windows: scripts\build.ps1
# Unix:    ./scripts/build.sh

VERSION     ?= 0.1.0
PYTHON      ?= python
JOBS        ?= 8
BUILD_DIR   ?= build
GUI_DIR     ?= src/core/GUI/py
RUST_DIR    ?= src/core/rs/mc-core
PYD         ?= $(GUI_DIR)/mc_core/_mc_core.pyd

.PHONY: help all rust cpp gui clean test

help:
	@echo MC Launcher build
	@echo.
	@echo   make all     rust + cpp
	@echo   make rust    build PyO3 extension
	@echo   make cpp     cmake build C++ core
	@echo   make gui     run PySide6 QML GUI
	@echo   make test    run python tests
	@echo   make clean   remove build/

all: rust cpp

rust:
ifeq ($(OS),Windows_NT)
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/cargo_build.ps1
else
	./scripts/cargo_build.sh
endif

cpp:
	cmake -S . -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=Release
	cmake --build $(BUILD_DIR) -j$(JOBS)

gui: rust
	cd $(GUI_DIR) && $(PYTHON) main_qml.py

test:
	$(PYTHON) -m pytest tests/python -q

clean:
ifeq ($(OS),Windows_NT)
	if exist $(BUILD_DIR) rmdir /s /q $(BUILD_DIR)
else
	rm -rf $(BUILD_DIR)
endif
