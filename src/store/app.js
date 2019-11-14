let connect = require('amqplib').connect(process.env.RABBIT_URL);
let queueName = 'store';
const MongoClient = require('mongodb').MongoClient;

// Connection URL
const url = 'mongodb://mongo:27017/fsbot';
var db = null;

MongoClient.connect(url, {useUnifiedTopology: true}, function(err, client) {
  console.log("Connected successfully to db server");
  db = client.db();
});

connect.then(con => {
    console.log('connection ready');
    return con.createChannel();
}).then(async ch => {
    await ch.assertQueue(queueName);
    await ch.bindQueue(queueName, 'topic', 'core.messageIn');
    ch.consume(queueName, function(msg) {
        if (msg !== null) {
            let event = JSON.parse(msg.content.toString());
            console.log('{Rabbit} <= ' + JSON.stringify(event));
            if (event.event === 'core.messageIn'){
                if (event.text === '/store_info'){
                    sendTxt(ch, event.chatid, _('Here will be info about storage'), []);
                } else if (event.text === '/store_increment'){
                    storeIncrement(ch, event);
                } else if (event.text === '/store_read'){
                    storeRead(ch, event);
                }
            } else {
                console.log('unknown event', event);
            }
            ch.ack(msg);
        }
    });
});

async function storeIncrement(ch, event){
    await db.collection('demo').findOneAndUpdate({
            id: 'counter',
        },{
            $inc: {val: 1}
        },{
            upsert: true,
        }
    );
    sendTxt(ch, event.chatid, _('Incremented'));
}

async function storeRead(ch, event){
    let counter = await db.collection('demo').findOne({id: 'counter'});
    let value = counter ? counter.val : 0;
    sendTxt(ch, event.chatid, _('Counter in db: %s'), [value]);
}

function sendTxt(ch, chatId, text, placeholders){
    let outcomeEvent = {
        event: 'call.translateAndSend',
        args: {
            chatId: chatId,
            text: text,
            placeholders: placeholders
        }
    };
    let outStr = JSON.stringify(outcomeEvent);
    console.log('{Rabbit} => ' + outStr);
    ch.publish('topic', outcomeEvent.event, Buffer.from(outStr, 'utf8'));
}

function _(msg){
    return msg;
}
