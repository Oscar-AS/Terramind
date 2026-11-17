# Contrôles locaux de TerraMind Afrique.
# Usage : make setup | lint | format | test | check-content
# Chaque cible ignore les parties du dépôt qui n'existent pas encore.

PYTHON ?= python
NODE_DIRS := channels/pwa dashboard

.PHONY: setup lint format test check-content

setup:
	$(PYTHON) -m pip install -r engine/requirements-dev.txt
	@if [ -f engine/requirements.txt ]; then $(PYTHON) -m pip install -r engine/requirements.txt; fi
	@for d in $(NODE_DIRS); do \
		if [ -f $$d/package.json ]; then (cd $$d && npm ci) || exit 1; fi; \
	done
	pre-commit install

lint:
	ruff check .
	black --check .
	$(PYTHON) scripts/check_hygiene.py
	@for d in $(NODE_DIRS); do \
		if [ -f $$d/package.json ]; then (cd $$d && npm run lint --if-present) || exit 1; fi; \
	done

format:
	ruff check --fix .
	black .

# pytest renvoie 5 quand aucun test n'est collecté : ce n'est pas un échec ici.
test:
	@$(PYTHON) -m pytest; status=$$?; \
	if [ $$status -eq 5 ]; then echo "Aucun test collecté."; exit 0; fi; exit $$status
	@for d in $(NODE_DIRS); do \
		if [ -f $$d/package.json ]; then (cd $$d && npm test --if-present) || exit 1; fi; \
	done

check-content:
	$(PYTHON) scripts/check_content.py
