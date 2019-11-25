const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');
const DEFAULT_CITY = 1;

module.exports = async function (event){
    let modeName = event.text.split(' ')[1];

    await mongo.collection('city').findOneAndUpdate({
        cityId: DEFAULT_CITY,
    },{
        $pull: {'modes': modeName}
    });

    sendText(event.chatid, _("Mode removed: %s"), [modeName]);
};