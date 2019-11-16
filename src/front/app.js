let connect = require('amqplib').connect(process.env.RABBIT_URL);
let queueName = 'front';

const TOKEN = process.env.TELEGRAM_TOKEN;
const TelegramBot = require('node-telegram-bot-api');
const bot = new TelegramBot(TOKEN, {polling: {interval: 1000}});

connect.then(con => {
    console.log('connection ready');
    return con.createChannel();
}).then(async ch => {
    await ch.assertQueue(queueName);
    await ch.bindQueue(queueName, 'topic', 'call.telegramSend');
    ch.consume(queueName, function(msg) {
        if (msg !== null) {
            let event = JSON.parse(msg.content.toString());
            console.log('{Rabbit} <= ' + JSON.stringify(event));
            if (event.event === 'call.telegramSend'){
                let args = event.args;
                bot.sendMessage(args.chatId, args.text);
            } else {
                console.log('unknown event', event);
            }
            ch.ack(msg);
        }
    });
    bot.on('message', function(msg){
        if (msg.chat.id < 0){
            return;
        }

        let decode_query = {
            "event": 'core.messageIn',
            "text": msg.text,
            "msgid": msg.message_id,
            "chatid": msg.from.id,
            "rawMsg": msg,
            "tg_name": get_tg_nick(msg)
        };
        send(ch, decode_query);

        console.log('msg.text', msg.text);

        if (msg.text === '/ping'){
            sendTxt(ch, msg.chat.id, _('Pong from %s'), ["front"]);
        }
    });
});

function get_tg_nick(msg){
    return msg.from.username || ('#' + msg.from.id);
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
    send(ch, outcomeEvent);
}

function send(ch, event){
    let outStr = JSON.stringify(event);
    console.log('{Rabbit} => ' + outStr);
    ch.publish('topic', event.event, Buffer.from(outStr, 'utf8'));
}

function _(msg){
    return msg;
}