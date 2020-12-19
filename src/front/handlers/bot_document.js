const {_} = require('flatground');
const proceedPhoto = require('./int_proceedPhoto');
const sendText = require('../sendText');
const IMG_MIME_TYPES = ['image/png', 'image/jpg', 'image/jpeg'];
const env = process.env;

module.exports = async function(msg){
    if (env.IMG_CHAT && IMG_MIME_TYPES.includes(msg.document.mime_type)){
        return proceedPhoto(msg);
    }
    sendText(msg.chat.id, _('Files are not allowed'));
}