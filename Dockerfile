FROM debian:stretch

RUN apt-get update && apt-get install -y python3-dev python3-pip

COPY . /root/api
WORKDIR /root/api/

RUN /usr/bin/pip3 install -r requirements.txt

EXPOSE 6667 8000

CMD ["/usr/bin/python3", "run.py"]
