# jinja2-git-dir Development Makefile
#
# Common tasks for development workflow.
#
# Lint targets auto-fix and fail if files were modified (for CI/hooks).

CURRENT_BRANCH := $(shell git branch --show-current)

.PHONY: help
.PHONY: install lint typecheck test build clean all release

# Default target - auto-generated from inline ## comments
help:
	@echo "jinja2-git-dir Development Commands ($(CURRENT_BRANCH))"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# CORE TARGETS
# ============================================================================

install: ## Install dependencies
	uv sync

lint: ## Lint (auto-fix ruff check + format)
	@echo "Running ruff check (auto-fix)..."
	uv run ruff check src/ tests/ --fix --exit-non-zero-on-fix
	@echo "Running ruff format (auto-fix)..."
	uv run ruff format src/ tests/ --exit-non-zero-on-format

typecheck: ## Run pyright type checking
	@echo "Running pyright..."
	uv run pyright src/

test: ## Run test suite
	@echo "Running pytest..."
	uv run pytest tests/ -v

build: ## Build sdist and wheel
	uvx hatch build

clean: ## Remove build artifacts and caches
	rm -rf .cache dist

all: install lint typecheck test ## Complete workflow: install → lint → typecheck → test

release: ## Tag and publish a new release (interactive, main branch only)
	@set -e; \
	GIT_DIR=$$(git rev-parse --git-dir); \
	if [ "$$GIT_DIR" != ".git" ]; then \
		echo "ERROR: Cannot release from a worktree. Run from the repo root."; \
		exit 1; \
	fi; \
	BRANCH=$$(git branch --show-current); \
	if [ "$$BRANCH" != "main" ]; then \
		echo "ERROR: Must be on main branch (currently on $$BRANCH)."; \
		exit 1; \
	fi; \
	git fetch --tags; \
	LATEST=$$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0"); \
	LATEST_CLEAN=$${LATEST#v}; \
	echo "Current version: $$LATEST"; \
	read -p "New version (X.Y.Z): " VERSION; \
	if ! echo "$$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$$'; then \
		echo "ERROR: Invalid semver format. Expected X.Y.Z (e.g., 1.2.3)."; \
		exit 1; \
	fi; \
	IFS='.' read -r MAJOR MINOR PATCH <<< "$$VERSION"; \
	IFS='.' read -r L_MAJ L_MIN L_PAT <<< "$$LATEST_CLEAN"; \
	if [ "$$VERSION" = "$$LATEST_CLEAN" ]; then \
		echo "ERROR: Version $$VERSION already exists (duplicate)."; \
		exit 1; \
	fi; \
	if [ "$$MAJOR" -lt "$$L_MAJ" ] || \
	   ([ "$$MAJOR" -eq "$$L_MAJ" ] && [ "$$MINOR" -lt "$$L_MIN" ]) || \
	   ([ "$$MAJOR" -eq "$$L_MAJ" ] && [ "$$MINOR" -eq "$$L_MIN" ] && [ "$$PATCH" -lt "$$L_PAT" ]); then \
		echo "ERROR: Version $$VERSION would be a downgrade from $$LATEST_CLEAN."; \
		exit 1; \
	fi; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	git push origin "v$$VERSION"; \
	gh release create "v$$VERSION" --generate-notes --title "v$$VERSION"
