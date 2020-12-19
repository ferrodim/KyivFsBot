const {_} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    sendText(event.chatid, _('Id of this chat is %s'), [event.chatid]);
};