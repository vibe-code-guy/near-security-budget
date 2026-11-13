# Standard library only: Python 3.9+ and nothing to install. No credentials anywhere.
PYTHON ?= python3

.PHONY: all build test data

# Rebuild every table and the dashboard data from the cached raw files, then run the tests. No network.
all: build test

build:
	$(PYTHON) -m pipeline build

test:
	$(PYTHON) -m unittest discover -s tests -q

# Refresh the raw cache (DefiLlama GETs and read-only NEAR view calls). Records retrieval time
# and block height in data/raw/manifest.json. The frozen universe is never changed by this.
data:
	$(PYTHON) -m pipeline data
