#!/bin/sh
# Use this script as hint, how to setup bot on fresh Ubuntu 18.04 environment
sudo -s
apt update
# apt dist-upgrade
apt upgrade
apt install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt update
apt install docker-ce docker-ce-cli containerd.io docker-compose git
git clone https://github.com/ferrodim/KyivFsBot.git
cd KyivFsBot/
cp config.sample.py config.py
vi config.py
docker-compose up -d
