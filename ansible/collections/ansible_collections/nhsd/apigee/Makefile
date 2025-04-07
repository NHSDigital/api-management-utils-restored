

update-schema:
	@PYTHONPATH=../../../ poetry run python scripts/update_schema.py

unit-test:
	@poetry run ansible-test units --python=3.8

integration-test:
	@poetry run ansible-test integration --python=3.8

test: unit-test integration-test

.PHONY: update-schema unit-test integration-test
