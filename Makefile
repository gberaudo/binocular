.venv/bin/python3 .venv/bin/pip:
	pyvenv .venv

.venv/bin/flake8: .requirements_timestamp

.requirements_timestamp: .venv/bin/pip requirements.txt
	.venv/bin/pip install -r requirements.txt
	@touch $@

flake8: .venv/bin/flake8
	.venv/bin/flake8 --ignore=E702,E402,E302 --max-line-length=120 server.py

.PHONY:
run: .requirements_timestamp flake8 config.ini .key_configured_timestamp .configured_timestamp
	.venv/bin/python3 server.py

key key.pub:
	@echo "Generating deploy keys"
	ssh-keygen -b 4096 -t rsa -N "" -C "demo deploy key" -f key

.key_configured_timestamp: config.ini key.pub
	@echo
	@echo "\033[1;34mOpen https://github.com/$(shell grep allowed config.ini | cut -f2 -d=)/settings/keys and add following deploy key\033[0m"
	cat key.pub
	@read -r -p "Press enter when done" unused
	@touch $@

config.ini: .venv/bin/python3
	scripts/configure.sh

.configured_timestamp: config.ini
	@echo
	@echo "\033[1;34mOpen https://github.com/$(shell grep allowed config.ini | cut -f2 -d=)/settings/hooks and add following (adapted) webhook\033[0m"
	@echo "http<s>://server_public_hostname_and_port/events (current server) with secret $(shell grep event_secret config.ini | cut -f2 -d=)"
	@read -r -p "Press enter when done" unused
	@touch $@

.PHONY:
clean:
	rm .*_timestamp
