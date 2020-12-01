const {_} = require('flatground');
const proceedPhoto = require('./int_proceedPhoto');
const sendText = require('../sendText');
const env = process.env;

module.exports = async function(msg){
    if (msg.chat.id < 0){
        return;
    }

    if (env.IMG_CHAT){
        return proceedPhoto(msg);
    }

    sendText(msg.chat.id, _('Image parsing disabled'));
}