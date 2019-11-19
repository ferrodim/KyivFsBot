const {mongo, _} = require('../framework');
const sendText = require('../sendText');

module.exports = async function storeRead(event){
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