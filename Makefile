PYTHON = python3	
CLEANUP_DIRS = .promptsite __pycache__ .pytest_cache .coverage .nox *.egg-info dist build .ruff_cache

lint: 
	@echo "Running Linter (Ruff and Black)..." 
	poetry run ruff format promptsite tests 
	poetry run ruff check promptsite tests 
	poetry run black promptsite tests 

test:
	@echo "Running tests with pytest..."
	poetry run pytest tests/ -cov=promptsite --disable-warnings -q -s

clean:
	@echo "Cleaning up build artifacts and cache..."
	rm -rf $(CLEANUP_DIRS)

install:
	@echo "Installing dependencies..."
	poetry install
	poetry run pre-commit install

build_docs:
	@echo "Building documentation..."
	mkdocs build

serve_docs:
	@echo "Serving documentation..."
	mkdocs serve


all: lint test clean