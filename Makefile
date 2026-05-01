.PHONY: setup brew-deps python-deps node-deps model test

setup: brew-deps python-deps node-deps model ## Full environment setup from scratch

brew-deps: ## Install system dependencies via Homebrew
	brew tap BRO3886/tap
	brew install ical rem-cli ollama
	brew services start ollama

python-deps: ## Install Python package and dependencies
	pip install -e .

node-deps: ## Install Node dependencies (gws-mcp-server)
	npm install

model: ## Pull the Ollama model for memory extraction
	ollama pull qwen2.5:7b

test: ## Run test suite
	python -m pytest tests/ -v
