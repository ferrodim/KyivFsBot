const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');

module.exports = async function (event){
    if (!event.isAdmin){
        sendText(event.chatid, _("This command allowed only for admins"));
        return;
    }

    let startTime = event.text.split(' ')[1];

    await mongo.collection('city').findOneAndUpdate({
        cityId: event.cityId,
    },{
        $set: {'startTime': startTime}
    }, {
        upsert: true
    });

    sendText(event.chatid, _("City info updated"));
};