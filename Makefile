SHELL:= /bin/bash

qa:
	$(MAKE) -C armasec-core qa
	$(MAKE) -C armasec-fastapi qa
	$(MAKE) -C armasec-cli qa

format:
	$(MAKE) -C armasec-core format
	$(MAKE) -C armasec-fastapi format
	$(MAKE) -C armasec-cli format

clean:
	$(MAKE) -C armasec-core cli
	$(MAKE) -C armasec-fastapi cli
	$(MAKE) -C armasec-cli cli
