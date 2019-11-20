const {mongo, _} = require('../framework');
const sendText = require('../sendText');

module.exports = async function (event){
    let admins = await mongo.collection('admin').find({}).toArray() || [];
    let adminLogins = admins.map(a => a.tgNick);

    if (adminLogins.length){
        sendText(event.chatid, _("Admin list:\n%s"), [adminLogins.map(a=>'☀@'+a).join("\n")]);
    } else {
        sendText(event.chatid, _("Admin list is empty"));
    }
};