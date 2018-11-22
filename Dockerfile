FROM debian:stretch

RUN apt-get update && apt-get install -y python3-dev python3-pip
RUN /usr/bin/pip3 install -r requirements.txt

COPY . /root/api

EXPOSE 6667 8000
WORKDIR /root/api/

CMD ["/usr/bin/python3", "run.py"]
