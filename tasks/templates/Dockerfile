FROM	python:3.9.6-alpine3.14 AS runner


COPY	requirements.txt  \
	/opt/

RUN	\
	pip install -r /opt/requirements.txt  &&\
	rm /opt/requirements.txt  &&\
	:


COPY	app.py   \
	start_app.sh  \
	flag.txt  \
	/app/

RUN	\
	chmod -R 000 /app/  &&\
	chmod a+rx /app/  &&\
	chmod a+r /app/flag.txt  &&\
	chmod a+r /app/app.py  &&\
	chmod a+rx /app/start_app.sh  &&\
	:

WORKDIR	/app/
CMD	["./start_app.sh"]
