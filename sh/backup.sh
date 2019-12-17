#!/bin/bash
apt install -y p7zip-full
docker-compose stop
mkdir out
docker-compose logs -t > out/docker.log
cp data/base.txt out/
cp config.py out/
history > out/bash.history.txt
mv out `date +"fs-kyiv-%Y-%m"`
7z a -mx=9 -mhe `date +"fs-kyiv-%Y-%m"`.7z `date +"fs-kyiv-%Y-%m"`