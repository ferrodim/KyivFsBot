const {_} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    let city = event.city;
    let fsName = city.fsName || '< FS NAME >'; // Kyiv - August 2020
    let startTime = city.startTime || '??';
    let endTime = city.endTime || '??';
    let template = _('Welcome to %s, export me your start data at *%s*, and finish data at *%s*. Also use [google form](%s). Write /help for more info');

    if (event.chatid < 0){
        return; // ignore txt messages in chat groups
    }

    sendText(event.chatid, template, [fsName, startTime, endTime, city.statUrl], true);
};