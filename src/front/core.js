const {mongo, _} = require('flatground');
const {translate, locales} = require('./services/lang');
const bot = require('./services/bot');

module.exports = {
    mongo, _,
    translate, locales,
    bot,
};