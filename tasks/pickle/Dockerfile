FROM	www-py_nsjail AS runner

RUN	apt-get update && apt-get install -y --no-install-recommends \
	python3 \
	&& rm -r /var/lib/apt/lists/*

COPY	nsjail.sh /opt/
COPY	main.py /app/
COPY	flag.txt /flag

RUN \
	addgroup --gid 1000 app &&\
	useradd --no-create-home --uid 1000 --gid app --shell /bin/false app &&\
	chmod 0444 /flag &&\
	chmod 0500 /opt/nsjail.sh &&\
	chmod 0555 /app/main.py &&\
	:

CMD	["/opt/nsjail.sh", "/app/main.py"]
