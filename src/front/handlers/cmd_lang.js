const {_} = require('flatground');
const sendText = require('../sendText');
const {db, locales} = require('../services/lang');

module.exports = async function (event){
    let newLang = event.text.split(' ')[1];
    if (newLang){
        if (locales.includes(newLang)){
            db.userLang[event.chatid] = newLang;
            // TODO: save in mongo
            sendText(event.chatid, _('Language changed to "%s"'), [newLang]);
        } else {
            sendText(event.chatid, _('Unknown language "%s"'), [newLang]);
        }
    } else {
        sendText(event.chatid, _('Current language is "%s"'), [event.userLang]);
    }
};