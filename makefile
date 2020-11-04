.PHONY: install_source
install_source:
	python3 -m pip install --user -e .

.PHONY: build_wheel
build_wheel:
	python3 setup.py bdist_wheel

.PHONY: install_wheel
install_wheel: build_wheel
	python3 -m pip install --user dist/bbar-0.1-py3-none-any.whl

.PHONY: clean
clean: 
	rm -rf dist build *.egg-info
