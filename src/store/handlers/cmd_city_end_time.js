const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');
const DEFAULT_CITY = 1;

module.exports = async function (event){
    let endTime = event.text.split(' ')[1];

    await mongo.collection('city').findOneAndUpdate({
        cityId: DEFAULT_CITY,
    },{
        $set: {'endTime': endTime}
    }, {
        upsert: true
    });

    sendText(event.chatid, _("City info updated"));
};