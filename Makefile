pre-commit: ## Check
	pre-commit run --all-files
.PHONY: pre-commit

build: ## Build wheel
	python setup.py bdist_wheel
.PHONY: build

help: ## Display this message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make [COMMAND] \033[36m\033[0m\n\nCommand:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
.PHONY: help
