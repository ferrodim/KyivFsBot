const {mongo, _} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    if (!event.isAdmin){
        sendText(event.chatid, _("This command allowed only for admins"));
        return;
    }

    let chunks = event.text.split(' ');
    chunks.shift(); // remove cmd part

    let fsName = chunks.join(' ');

    await mongo.collection('city').findOneAndUpdate({
        cityId: event.cityId,
    },{
        $set: {'fsName': fsName}
    }, {
        upsert: true
    });

    sendText(event.chatid, _("City info updated"));
};