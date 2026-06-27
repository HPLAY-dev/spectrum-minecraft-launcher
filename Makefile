# SerenaLauncher — build shortcuts
# Windows: scripts\build.ps1
# Unix:    ./scripts/build.sh

VERSION     ?= 26Q2
BUILD_ID    ?= 0
PYTHON      ?= python
JOBS        ?= 8
BUILD_DIR   ?= build
GUI_DIR     ?= src/core/GUI/py
RUST_DIR    ?= src/core/rs/mc-core
PYD         ?= $(GUI_DIR)/mc_core/_mc_core.pyd

.PHONY: help all rust cpp gui version clean test

help:
	@echo SerenaLauncher build (Okra / major 26)
	@echo.
	@echo   make all      version + rust + cpp
	@echo   make version  generate 26Q2.BuildID.commitid
	@echo   make rust     build PyO3 extension
	@echo   make cpp      cmake build C++ core
	@echo   make gui      run PySide6 QML GUI
	@echo   make test     run python tests
	@echo   make clean    remove build/

all: version rust cpp

version:
ifeq ($(OS),Windows_NT)
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/gen_version.ps1
else
	SERENA_BUILD_ID=$(BUILD_ID) ./scripts/gen_version.sh
endif

rust: version
ifeq ($(OS),Windows_NT)
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/cargo_build.ps1
else
	./scripts/cargo_build.sh
endif

cpp: version
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
