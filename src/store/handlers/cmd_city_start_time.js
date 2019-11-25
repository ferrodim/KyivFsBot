const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');
const DEFAULT_CITY = 1;

module.exports = async function (event){
    let startTime = event.text.split(' ')[1];

    await mongo.collection('city').findOneAndUpdate({
        cityId: DEFAULT_CITY,
    },{
        $set: {'startTime': startTime}
    }, {
        upsert: true
    });

    sendText(event.chatid, _("City info updated"));
};