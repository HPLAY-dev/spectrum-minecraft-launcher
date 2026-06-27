# Spectrum Minecraft Launcher — Nuitka build
# Windows: make.bat all VERSION=1.0.0
# Unix:    make all VERSION=1.0.0

VERSION     ?= 1.0.0
NUITKA      ?= $(PYTHON) make_tools.py nuitka
PYTHON      ?= python
JOBS        ?= 16
ENTRY       ?= main.py
BUILD_DIR   ?= build
DIST_NAME   ?= nuitka-$(VERSION)
DIST_DIR    ?= builds/$(DIST_NAME)
ARCHIVE     ?= builds/$(DIST_NAME)-windows.7z
PYD         ?= python/spectrum_core/_spectrum_core.pyd

NUITKA_BASE = --mingw64 \
	--standalone \
	--jobs=$(JOBS) \
	--enable-plugin=pyside6 \
	--include-package=spectrum_core \
	--include-package=modrinth_api_wrapper \
	--include-data-dir=./assets=assets \
	--include-data-dir=./languages=languages \
	--assume-yes-for-downloads \
	--output-dir=$(BUILD_DIR) \
	--show-progress \
	--windows-console-mode=disable \
	--windows-file-version=$(VERSION) \
	--windows-product-version=$(VERSION) \
	--windows-file-description=Spectrum Minecraft Launcher

ifneq (,$(wildcard $(PYD)))
NUITKA_FLAGS = $(NUITKA_BASE) \
	--include-data-files=$(PYD)=python/spectrum_core/_spectrum_core.pyd
else
NUITKA_FLAGS = $(NUITKA_BASE)
endif

ifeq ($(OS),Windows_NT)
	RUST_BUILD = powershell -NoProfile -ExecutionPolicy Bypass -File cargo_build.ps1
	SHELL = cmd.exe
.SHELLFLAGS = /c
	RM = if exist $(BUILD_DIR) rmdir /s /q $(BUILD_DIR)
	MKDIST = if not exist builds mkdir builds & if exist $(DIST_DIR) rmdir /s /q $(DIST_DIR) & mkdir $(DIST_DIR)
	COPY_DIST = xcopy /E /I /Q $(BUILD_DIR)\main.dist $(DIST_DIR)
	COPY_ASSETS = xcopy /E /I /Q assets $(DIST_DIR)\assets
	COPY_LANG = xcopy /E /I /Q languages $(DIST_DIR)\languages
	ARCHIVE_CMD = 7z a -mx0 $(ARCHIVE) $(DIST_DIR)
else
	RUST_BUILD = cd spectrum-core && PYO3_PYTHON=$(PYTHON) cargo build --release --features python
	RM = rm -rf $(BUILD_DIR)
	MKDIST = rm -rf $(DIST_DIR) && mkdir -p $(DIST_DIR)
	COPY_DIST = cp -r $(BUILD_DIR)/main.dist/. $(DIST_DIR)/
	COPY_ASSETS = cp -r assets $(DIST_DIR)/
	COPY_LANG = cp -r languages $(DIST_DIR)/
	ARCHIVE_CMD = 7z a -mx0 $(ARCHIVE) $(DIST_DIR)
endif

.PHONY: help all clean rust ui nuitka dist archive

help:
	@echo Spectrum Launcher — Nuitka build
	@echo.
	@echo   make all              rust + ui + nuitka + dist + archive
	@echo   make nuitka           compile standalone bundle
	@echo   make dist             copy build output to builds/nuitka-VERSION
	@echo   make archive          create 7z release archive
	@echo   make rust             build PyO3 extension (optional)
	@echo   make ui               regenerate ui.py from qt.ui
	@echo   make clean            remove build/
	@echo.
	@echo   VERSION=1.0.0 make all

all: archive

archive: dist
	$(ARCHIVE_CMD)

dist: nuitka
	$(MKDIST)
	$(COPY_DIST)
	$(COPY_ASSETS)
	$(COPY_LANG)

nuitka: rust ui
	PYTHONPATH=python $(NUITKA) $(NUITKA_FLAGS) $(ENTRY)

rust:
	$(RUST_BUILD)

ui:
	$(PYTHON) make_tools.py uic -o ui.py qt.ui

clean:
	$(RM)
