const {mongo, _} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    if (!event.isAdmin){
        sendText(event.chatid, _("This command allowed only for admins"));
        return;
    }

    let tgNick = event.text.split(' ')[1];

    await mongo.collection('admin').insert({
        tgNick: tgNick
    });

    sendText(event.chatid, _("Admin added: %s"), [tgNick]);
};