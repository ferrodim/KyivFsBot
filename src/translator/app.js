let connect = require('amqplib').connect(process.env.RABBIT_URL);
let queueName = 'translator';
let db = {userLang: {}};
let allowedLangs = {"en": true, "ru": true, "ua": true};
const DEFAULT_LANG = 'en';

connect.then(con => {
    console.log('connection ready');
    return con.createChannel();
}).then(async ch => {
    await ch.assertQueue(queueName);
    await ch.bindQueue(queueName, 'topic', 'call.translateAndSend');
    await ch.bindQueue(queueName, 'topic', 'call.setLang');
    await ch.bindQueue(queueName, 'topic', 'core.messageIn');
    ch.consume(queueName, function(msg) {
        if (msg !== null) {
            let event = JSON.parse(msg.content.toString());
            console.log('{Rabbit} <= ' + JSON.stringify(event));
            if (event.event == 'call.translateAndSend'){
                sendTxt(ch, event.args.chatId, event.args.text);
            } else if (event.event == 'call.translateAndSend'){
                // db.userLang
            } else if (event.event == 'core.messageIn'){
                if (event.text.indexOf('/lang ') === 0){
                    let newLang = event.text.split(' ')[1];
                    if (allowedLangs[newLang]){
                        db.userLang[event.chatid] = newLang;
                        sendTxt(ch, event.chatid, 'Language changed to "%s"', [newLang]);
                    } else {
                        sendTxt(ch, event.chatid, 'Unknown language "%s"', [newLang]);
                    }
                }
            } else {
                console.log('unknown event', event);
            }


            ch.ack(msg);
        }
    });
});

function sendTxt(ch, chatId, text, placeholders){
    let userLang = db.userLang[chatId] || 'en';
    let outcomeEvent = {
        event: 'call.telegramSend',
        args: {
            chatId: chatId,
            text: translate(text, userLang, placeholders)
        }
    };
    let outStr = JSON.stringify(outcomeEvent);
    console.log('{Rabbit} => ' + outStr);
    ch.publish('topic', outcomeEvent.event, Buffer.from(outStr, 'utf8'));
}

var translateData = {
   "hello": {ru: "привет", ua: "привіт"},
   'Language changed to "%s"': {ru: 'Язык изменён на "%s"', ua: 'Мову змінено на "%s"'},
   'Unknown language "%s"': {ru: 'Неизвестный язык "%s"', ua: 'Невідома мова "%s"'},
   'That user is not found in database': {
       ru: 'Такой пользователь не найден в базе',
       ua: 'Такий користувач не знайдений в базі'
   }
};

function translate(text, lang, placeholders){
    if (!lang){
        lang = 'en';
    }
    if (translateData[text] && translateData[text][lang]){
        text = translateData[text][lang];
    } else if (lang !== DEFAULT_LANG){
        text = '['+ lang + '] ' + text;
    }
    if (Array.isArray(placeholders)){
        for (let placeholder of placeholders){
            text = text.replace('%s', placeholder);
        }
    }
    return text;
}
