

update-schema:
	@PYTHONPATH=../../../ poetry run python scripts/update_schema.py

unit-test:
	@poetry run ansible-test units --python=3.10

integration-test:
	@poetry run ansible-test integration --python=3.10

test: unit-test integration-test

.PHONY: update-schema unit-test integration-test
