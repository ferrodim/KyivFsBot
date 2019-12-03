const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');

module.exports = async function (event){
    if (!event.isAdmin){
        sendText(event.chatid, _("This command allowed only for admins"));
        return;
    }
    let modeName = event.text.split(' ')[1];

    await mongo.collection('city').findOneAndUpdate({
        cityId: event.cityId,
    },{
        $addToSet: {'modes': modeName}
    }, {
        upsert: true
    });

    sendText(event.chatid, _("Mode added: %s"), [modeName]);
};