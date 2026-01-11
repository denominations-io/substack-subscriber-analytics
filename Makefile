# Makefile for Substack Subscriber Analytics
# Supports Windows, macOS, and Linux

# Detect operating system
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    VENV := venv
    PYTHON := $(VENV)\Scripts\python.exe
    PIP := $(VENV)\Scripts\pip.exe
    STREAMLIT := $(VENV)\Scripts\streamlit.exe
    ACTIVATE := $(VENV)\Scripts\activate.bat
    VENV_EXISTS := if exist $(VENV) (echo exists)
    MKDIR_VENV := python -m venv $(VENV)
    RM_VENV := if exist $(VENV) rmdir /s /q $(VENV)
    TOUCH := type nul >
    SEP := \\
else
    DETECTED_OS := $(shell uname -s)
    VENV := venv
    PYTHON := $(VENV)/bin/python
    PIP := $(VENV)/bin/pip
    STREAMLIT := $(VENV)/bin/streamlit
    ACTIVATE := $(VENV)/bin/activate
    VENV_EXISTS := test -d $(VENV)
    MKDIR_VENV := python3 -m venv $(VENV)
    RM_VENV := rm -rf $(VENV)
    TOUCH := touch
    SEP := /
endif

.PHONY: run install clean help info

# Default target
help:
	@echo "Substack Subscriber Analytics - Makefile Commands"
	@echo ""
	@echo "  make install  - Create virtual environment and install dependencies"
	@echo "  make run      - Start the Streamlit application"
	@echo "  make clean    - Remove virtual environment"
	@echo "  make info     - Show detected OS and paths"
	@echo ""
	@echo "Detected OS: $(DETECTED_OS)"

# Show environment info
info:
	@echo "Detected OS: $(DETECTED_OS)"
	@echo "Python: $(PYTHON)"
	@echo "Pip: $(PIP)"
	@echo "Streamlit: $(STREAMLIT)"
	@echo "Virtual env: $(VENV)"

# Run the Streamlit application
run: install
	$(STREAMLIT) run app.py

# Install dependencies (creates venv if needed)
ifeq ($(OS),Windows_NT)
install: requirements.txt
	@if not exist $(VENV) ( \
		echo Creating virtual environment... && \
		$(MKDIR_VENV) \
	)
	$(PIP) install -r requirements.txt
	@echo Installation complete!
else
install: requirements.txt
	@if [ ! -d $(VENV) ]; then \
		echo "Creating virtual environment..."; \
		$(MKDIR_VENV); \
	fi
	$(PIP) install -r requirements.txt
	@echo "Installation complete!"
endif

# Clean up virtual environment
clean:
ifeq ($(OS),Windows_NT)
	@if exist $(VENV) rmdir /s /q $(VENV)
	@echo Virtual environment removed.
else
	@rm -rf $(VENV)
	@echo "Virtual environment removed."
endif
