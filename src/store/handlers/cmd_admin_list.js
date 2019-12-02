const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');

module.exports = async function (event){
    if (!event.isAdmin){
        sendText(event.chatid, _("This command allowed only for admins"));
        return;
    }

    let admins = await mongo.collection('admin').find({}).toArray() || [];
    let adminLogins = admins.map(a => a.tgNick);

    if (adminLogins.length){
        sendText(event.chatid, _("Admin list:\n%s"), [adminLogins.map(a=>'☀@'+a).join("\n")]);
    } else {
        sendText(event.chatid, _("Admin list is empty"));
    }
};