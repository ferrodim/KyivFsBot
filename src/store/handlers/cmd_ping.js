const {_} = require('../framework');
const sendText = require('../sendText');

module.exports = async function storeRead(event){
    sendText(event.chatid, _('Pong from %s'), ["store"]);
};