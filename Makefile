
all:

generate: generate-server generate-apidoc

generate-server:
	go-raml server -l python --kind flask --dir zerorobot/server --ramlfile api_spec/main.raml --api-file-per-method

generate-apidoc:
	if ! pip show pdoc > /dev/null; then pip install pdoc; fi
	rm -r docs/api
	pdoc --html  --html-dir docs/api --all-submodules --overwrite zerorobot

test:
	nose2 --with-coverage --coverage zerorobot

test-ui:
	nose2 --with-coverage --coverage-report html --coverage zerorobot
