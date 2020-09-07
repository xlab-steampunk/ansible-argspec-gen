.PHONY: clean
clean:
	rm -rf build dist

.PHONY: build
build: clean
	python3 setup.py sdist bdist_wheel

.PHONY: upload
upload: env-guard-TWINE_USERNAME env-guard-TWINE_PASSWORD
	twine check dist/*
	twine upload dist/*

env-guard-%:
	@ if [ "${${*}}" = "" ]; then \
	  echo "Environment variable $* not set"; \
	  exit 1; \
	fi
