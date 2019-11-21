const {mongo, _} = require('../../shared/framework');
const sendText = require('../sendText');

module.exports = async function (event){
    await mongo.collection('demo').findOneAndUpdate({
            id: 'counter',
        },{
            $inc: {val: 1}
        },{
            upsert: true,
        }
    );
    sendText(event.chatid, _('Incremented'));
};