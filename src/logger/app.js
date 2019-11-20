let connect = require('amqplib').connect(process.env.RABBIT_URL);
let queueName = 'logger';

connect.then(con => {
    console.log('connection ready');
    return con.createChannel();
}).then(async ch => {
    await ch.assertQueue(queueName);
    await ch.bindQueue(queueName, 'topic', 'parseResult');
    await ch.bindQueue(queueName, 'topic', 'core.*');
    await ch.bindQueue(queueName, 'topic', 'call.*');
    ch.consume(queueName, function(msg) {
        if (msg !== null) {
            // console.log(msg.content.toString());
            let event = JSON.parse(msg.content.toString());
            console.log('{Rabbit} <= ' + JSON.stringify(event));
            if (event.text === '/ping'){
                sendTxt(ch, event.chatid, _('Pong from %s'), ["logger"]);
            }
            ch.ack(msg);
        }
    });
});

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