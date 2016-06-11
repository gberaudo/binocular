.venv/bin/python3 .venv/bin/pip:
	pyvenv .venv
	.venv/bin/pip install wheel

.venv/bin/flake8: .requirements_timestamp

.requirements_timestamp: .venv/bin/pip requirements.txt
	.venv/bin/pip install -r requirements.txt
	@touch $@

flake8: .venv/bin/flake8
	.venv/bin/flake8 --ignore=E702,E402,E302 --max-line-length=130 server.py

.PHONY:
run: .requirements_timestamp flake8 config.ini .key_configured_timestamp .configured_timestamp
	.venv/bin/python3 server.py

key key.pub:
	@echo "Generating deploy keys"
	ssh-keygen -b 4096 -t rsa -N "" -C "demo deploy key" -f key

.key_configured_timestamp: config.ini key.pub
	@echo
	@echo "If your repository is private, you need an asymetric deploy key pair to clone from github"
	@echo "\033[1;34mOpen https://github.com/$(shell grep allowed config.ini | cut -f2 -d=)/settings/keys and add following deploy key\033[0m"
	cat key.pub
	@read -r -p "Press enter when done" unused
	@touch $@

config.ini:
	@echo "Please configure a project as explained in README.md"
	@exit 1

.configured_timestamp: config.ini
	@echo
	@echo "In order for github to notify binocular of events occuring your repository you need to setup the public URL to binocular"
	@echo "\033[1;34mOpen https://github.com/$(shell grep allowed config.ini | cut -f2 -d=)/settings/hooks and add following (adapted) webhook\033[0m"
	@echo "http<s>://server_public_hostname_and_port/events (current server) with secret $(shell grep event_secret config.ini | cut -f2 -d=)"
	@read -r -p "Press enter when done" unused
	@touch $@

.PHONY:
clean:
	rm .*_timestamp

.PHONY:
cleanall: clean
	rm -rf .venv
