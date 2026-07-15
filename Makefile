# SPDX-License-Identifier: MIT-0
PYTHON := .venv/bin/python
RUFF := .venv/bin/ruff

.PHONY: setup format lint typecheck test coverage package terraform-init terraform-fmt terraform-validate terraform-test security check markdown demo-local-ocsf demo-local-asff clean

setup:
	python3.13 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e . --no-deps

format:
	$(RUFF) format src tests scripts
	$(RUFF) check --fix src tests scripts
	terraform -chdir=terraform fmt -recursive

lint:
	$(RUFF) format --check src tests scripts
	$(RUFF) check src tests scripts

typecheck:
	$(PYTHON) -m mypy

test:
	AWS_DEFAULT_REGION=us-east-1 AWS_EC2_METADATA_DISABLED=true $(PYTHON) -m pytest

coverage: test

package:
	bash scripts/build_lambda.sh

terraform-init:
	terraform -chdir=terraform init -backend=false

terraform-fmt:
	terraform -chdir=terraform fmt -check -recursive

terraform-validate: terraform-init
	terraform -chdir=terraform validate

terraform-test: terraform-init
	AWS_EC2_METADATA_DISABLED=true terraform -chdir=terraform test

markdown:
	npx --yes markdownlint-cli2@0.18.1 '**/*.md' '!**/.venv/**' '!**/.terraform/**'

security:
	$(PYTHON) -m pip_audit -r requirements.txt
	tflint --chdir=terraform --init --config="$(CURDIR)/.tflint.hcl"
	tflint --chdir=terraform --recursive --config="$(CURDIR)/.tflint.hcl"
	trivy config --exit-code 1 --severity HIGH,CRITICAL terraform

check: lint typecheck test package terraform-fmt terraform-validate terraform-test security markdown

demo-local-ocsf:
	AWS_DEFAULT_REGION=us-east-1 AWS_EC2_METADATA_DISABLED=true PYTHONPATH=src $(PYTHON) scripts/invoke_local.py fixtures/ocsf/high-severity.json --mode ocsf

demo-local-asff:
	AWS_DEFAULT_REGION=us-east-1 AWS_EC2_METADATA_DISABLED=true PYTHONPATH=src $(PYTHON) scripts/invoke_local.py fixtures/asff/high-severity.json --mode asff

clean:
	rm -rf build .coverage .pytest_cache .mypy_cache .ruff_cache
