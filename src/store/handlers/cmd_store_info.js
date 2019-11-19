const {mongo, _} = require('../framework');
const sendText = require('../sendText');

module.exports = async function storeRead(event){
    sendText(event.chatid, _('Here will be info about storage'));
};