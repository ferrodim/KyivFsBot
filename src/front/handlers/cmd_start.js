const {_} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    let city = event.city;
    let startTime = city.startTime || '??';
    let endTime = city.endTime || '??';
    // let modes = city.modes || [];
    let template = _('Welcome, export me your start data at *%s*, and finish data at *%s*. Also use [google form](%s). Write /help for more info');
    sendText(event.chatid, template, [startTime, endTime, city.statUrl], true);
};