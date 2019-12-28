const {mongo, _} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    sendText(event.chatid, _('Here will be info about storage'));
};