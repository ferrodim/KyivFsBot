const {mongo, _} = require('flatground');
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
        $pull: {'modes': modeName}
    });

    sendText(event.chatid, _("Mode removed: %s"), [modeName]);
};