#!/bin/bash
apt update -y
apt upgrade -y
apt install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt update -y
apt install -y docker-ce docker-ce-cli containerd.io docker-compose git
git clone https://github.com/ferrodim/KyivFsBot.git
cd KyivFsBot/
cp config.sample.py config.py
echo 'Edit config.py as you wish and then start bot with "docker-compose up -d"'
