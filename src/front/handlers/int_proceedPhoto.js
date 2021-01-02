const {mongo, _} = require('flatground');
const bot = require('../services/bot');
const sendText = require('../sendText');
const env = process.env;

module.exports = async function proceedPhoto(msg){
    if (!msg.caption){
        sendText(msg.chat.id, _('Image must have a caption'));
        return;
    }
    if (!msg.caption.match(/^[a-zA-Z0-9_]+$/)){
        sendText(msg.chat.id, _('Image caption must be your nickname'));
        return;
    }
    await bot.forwardMessage(env.IMG_CHAT, msg.chat.id, msg.message_id);

    await mongo.collection('log').insert({
        type: 'imageForwarded',
        chatId: msg.chat.id,
        msgId: msg.message_id,
        date: Date.now(),
        caption: msg.caption,
    });

    sendText(msg.chat.id, _('Image forwarded'));
}