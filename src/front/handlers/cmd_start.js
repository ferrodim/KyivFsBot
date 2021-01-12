const {_} = require('flatground');
const {translate} = require('../services/lang');
const bot = require('../services/bot');

module.exports = async function (event){
    let city = event.city;
    let fsName = city.fsName || '< FS NAME >'; // Like Kyiv - August 2020
    let startTime = city.startTime || '??';
    let endTime = city.endTime || '??';
    let text = _('Welcome to %s, export me your start data at *%s*, and finish data at *%s*. Also use [google form](%s). Write /help for more info');

    if (event.chatid < 0){
        return; // ignore txt messages in chat groups
    }

    let msg = translate(text, event.userLang, [fsName, startTime, endTime, city.statUrl]);
    await bot.sendMessage(event.chatid, msg, {
        parse_mode: 'Markdown',
    });
};