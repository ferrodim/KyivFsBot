const {_} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    if (!event.isAdmin){
        return;
    }
    sendText(event.chatid, _('Pong from %s'), ["front"]);
};