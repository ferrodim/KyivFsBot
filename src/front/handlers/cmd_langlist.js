const {_} = require('flatground');
const sendText = require('../sendText');
const {locales} = require('../services/lang');

module.exports = async function (event){
    sendText(event.chatid, _('List of languages: %s'), [locales.join()]);
};