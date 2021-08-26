FROM	python:3.9.6-alpine3.14 AS runner


COPY	requirements.txt  \
	/opt/

RUN	\
	pip install -r /opt/requirements.txt  &&\
	rm /opt/requirements.txt  &&\
	:


COPY	app.py   \
	start_app.sh  \
	/app/

RUN	\
	chmod -R 000 /app/  &&\
	chmod a+rx /app/  &&\
	chmod a+r /app/app.py  &&\
	chmod a+rx /app/start_app.sh  &&\
	:

ENV	FLAG=WWW{where-you-stand-depends-on-where-you-sit-2}
WORKDIR	/app/
CMD	["./start_app.sh"]
