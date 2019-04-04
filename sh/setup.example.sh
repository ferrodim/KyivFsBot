#!/bin/sh
# Use this script as hint, how to setup bot on fresh Ubuntu 16.04 environment 
sudo -s
apt update
apt dist-upgrade
apt upgrade
apt install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt update

install docker-ce docker-ce-cli containerd.io
apt install docker-ce docker-ce-cli containerd.io
docker run hello-world
apt install docker-compose
apt install git
git clone https://github.com/ferrodim/KyivFsBot.git
cd KyivFsBot/
vi config.py
docker-compose up -d
