
const env = process.env;
const TelegramBot = require('node-telegram-bot-api');
const bot = new TelegramBot(env.TELEGRAM_TOKEN, {polling: {interval: 1000}});

module.exports = bot;