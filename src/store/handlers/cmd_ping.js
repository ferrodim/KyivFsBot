const {_} = require('../framework');
const sendText = require('../sendText');

module.exports = async function (event){
    sendText(event.chatid, _('Pong from %s'), ["store"]);
};