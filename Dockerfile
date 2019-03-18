FROM ubuntu:18.10
RUN mkdir -p /code/Screens && chmod +w /code/Screens
WORKDIR /code
RUN apt update && apt install -y \
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
RUN pwd
RUN ls -l
COPY requirements.txt  /code
RUN pip3 install -r /code/requirements.txt
RUN wget https://github.com/tesseract-ocr/tesseract/archive/3.05.00.tar.gz &&\
  tar -xf 3.05.00.tar.gz &&\
  cd tesseract-3.05.00/ &&\
  ./autogen.sh &&\
  ./configure --enable-debug LDFLAGS="-L/usr/local/lib" CFLAGS="-I/usr/local/include" &&\
  make && make install && ldconfig
RUN wget https://raw.githubusercontent.com/tesseract-ocr/tessdata/3.04.00/eng.traineddata && mv eng.traineddata /usr/local/share/tessdata/
CMD ["bash", "start.sh"]