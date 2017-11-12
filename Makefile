run:
	raco superv discord-config.json
virtualenv:
	virtualenv dev
setup:
	pip install -r requirements.txt
	raco pkg install superv
clean:
	rm -rf botdata/
test:
	sh tests.sh
copy_keys:
	scp -r keys steve@alarmpi:~/discord-bots
kill:
	kill $$(ps aux | grep rack | grep discord-config.json | awk '{print $$2}')
format:
	autopep8 -i -r bots/ -aa -vv
