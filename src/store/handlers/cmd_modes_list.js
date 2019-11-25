const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');
const DEFAULT_CITY = 1;

module.exports = async function (event){
    let city = await mongo.collection('city').findOne({cityId: DEFAULT_CITY});

    if (city && Array.isArray(city.modes) && city.modes.length){
        sendText(event.chatid, _("Active modes:\n%s"), [city.modes.join()]);
    } else {
        sendText(event.chatid, _("No active modes"));
    }
};