.PHONY: all test report pipeline pam-sources pam-pipeline sources clean

PYTHON ?= python3

all: test report pipeline pam-demo

test:
	$(PYTHON) -m pytest -q

report:
	$(PYTHON) -m analyse_qualite

pipeline:
	$(PYTHON) -m pipeline

pam-sources:
	$(PYTHON) -m pam_pipeline.generate_sources

pam-pipeline:
	$(PYTHON) -m pam_pipeline

pam-demo:
	$(PYTHON) -m pam_pipeline --generate-sources

sources:
	$(PYTHON) generate_erp_data.py
	$(PYTHON) -m pipeline.generate_sources
	$(PYTHON) -m pam_pipeline.generate_sources

clean:
	rm -f erp_migration.db changelog.db rapport_qualite.html pam_mobilite.db pam_quality_report.html pam_changelog.db pam_alerts.json
	rm -rf logs
