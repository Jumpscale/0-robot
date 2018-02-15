
all:

generate: generate-server generate-apidoc

generate-server:
	go-raml server -l python --kind flask --dir zerorobot/server --ramlfile api_spec/main.raml
	raml2html -p api_spec/main.raml > api_spec/api.html

generate-apidoc:
	if ! pip show pdoc > /dev/null; then pip install pdoc; fi
	rm -r docs/api
	pdoc --html  --html-dir docs/api --all-submodules --overwrite zerorobot

package: source_pkg bin_pkg

source_pkg:
	python3 setup.py sdist

bin_pkg:
	python3 setup.py bdist_wheel

test:
	pytest --cov=./ tests -v

test-ui:
	pytest --cov=./ --cov-report=html tests -v


.PHONY: all generate generate-server generate-apidoc package source_pkg bin_pkg test test-ui