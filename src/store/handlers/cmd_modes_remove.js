const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');

module.exports = async function (event){
    let modeName = event.text.split(' ')[1];

    await mongo.collection('city').findOneAndUpdate({
        cityId: event.cityId,
    },{
        $pull: {'modes': modeName}
    });

    sendText(event.chatid, _("Mode removed: %s"), [modeName]);
};