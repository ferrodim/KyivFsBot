const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');

module.exports = async function (event){
    if (!event.isAdmin){
        sendText(event.chatid, _("This command allowed only for admins"));
        return;
    }
    let city = await mongo.collection('city').findOne({cityId: event.cityId});

    if (city && Array.isArray(city.modes) && city.modes.length){
        sendText(event.chatid, _("Active modes:\n%s"), [city.modes.join()]);
    } else {
        sendText(event.chatid, _("No active modes"));
    }
};