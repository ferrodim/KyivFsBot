#!/bin/bash
apt update -y
apt upgrade -y
apt install -y docker-compose
git clone https://github.com/ferrodim/KyivFsBot.git
cd KyivFsBot/
cp .env.sample .env
echo 'Edit .env as you wish and then start bot with "docker-compose up -d"'
