FROM ubuntu:18.10
RUN mkdir /code
WORKDIR /code
RUN apt update && apt install -y \
  python3-pip
COPY requirements.txt  /
RUN pip3 install -r /requirements.txt && rm /requirements.txt
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
CMD ["bash", "/app/start.sh"]