FROM ubuntu:18.10
RUN mkdir /code
WORKDIR /code
RUN apt update && apt install -y \
  python3.6 \
  python3-pip \
  autoconf \
  automake \
  libtool \
  autoconf-archive \
  pkg-config \
  libpng-dev \
  libjpeg8-dev \
  libtiff5-dev \
  zlib1g-dev \
  libicu-dev \
  libpango1.0-dev \
  libcairo2-dev \
  libleptonica-dev \
  wget
RUN wget https://github.com/tesseract-ocr/tesseract/archive/3.05.00.tar.gz &&\
  tar -xf 3.05.00.tar.gz &&\
  cd tesseract-3.05.00/ &&\
  ./autogen.sh &&\
  ./configure --enable-debug LDFLAGS="-L/usr/local/lib" CFLAGS="-I/usr/local/include" &&\
  make && make install && ldconfig &&\
  cd .. && rm -rf tesseract-3.05.00/
RUN wget https://raw.githubusercontent.com/tesseract-ocr/tessdata/3.04.00/eng.traineddata && mv eng.traineddata /usr/local/share/tessdata/
COPY requirements.txt  /
RUN pip3 install -r /requirements.txt && rm /requirements.txt
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
CMD ["bash", "/app/start.sh"]