const {mongo, rabbit, _} = require('./framework');
const APP_NAME = 'store';

Promise.all([
    mongo.configure({
        url: process.env.MONGO_URL
    }),
    rabbit.configure({
        url: process.env.RABBIT_URL,
    }),
]).then(async () => {
    await rabbit.bind(APP_NAME, 'core.messageIn', function(event) {
        if (event.text === '/store_info'){
            sendTxt(event.chatid, _('Here will be info about storage'), []);
        } else if (event.text === '/store_increment'){
            storeIncrement(event);
        } else if (event.text === '/store_read'){
            storeRead(event);
        } else if (event.text === '/ping'){
            sendTxt(event.chatid, _('Pong from %s'), ["store"]);
        }
    });
});

async function storeIncrement(event){
    await mongo.collection('demo').findOneAndUpdate({
            id: 'counter',
        },{
            $inc: {val: 1}
        },{
            upsert: true,
        }
    );
    sendTxt(event.chatid, _('Incremented'));
}

async function storeRead(event){
    let counter = await mongo.collection('demo').findOne({id: 'counter'});
    let value = counter ? counter.val : 0;
    sendTxt(event.chatid, _('Counter in db: %s'), [value]);
}

function sendTxt(chatId, text, placeholders){
    let outcomeEvent = {
        event: 'call.translateAndSend',
        args: {
            chatId: chatId,
            text: text,
            placeholders: placeholders
        }
    };
    rabbit.emit(outcomeEvent);
}

