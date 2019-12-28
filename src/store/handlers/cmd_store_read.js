const {mongo, _} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    let counter = await mongo.collection('demo').findOne({id: 'counter'});
    let value = counter ? counter.val : 0;
    sendText(event.chatid, _('Counter in db: %s'), [value]);
};