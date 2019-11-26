const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');

module.exports = async function (event){
    let endTime = event.text.split(' ')[1];

    await mongo.collection('city').findOneAndUpdate({
        cityId: event.cityId,
    },{
        $set: {'endTime': endTime}
    }, {
        upsert: true
    });

    sendText(event.chatid, _("City info updated"));
};