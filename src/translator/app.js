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
                if (event.text == '/lang'){
                    sendTxt(ch, event.chatid, 'Current language is "%s"', [getUserLang(event.chatid)]);
                }
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

function getUserLang(chatId){
    return db.userLang[chatId] || 'en';
}

function sendTxt(ch, chatId, text, placeholders){
    let userLang = getUserLang(chatId);
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
   },
   'Image retrieved': {
       en: '⏳ Image retreived\n\nPlease, send text statistic next time',
       ru: "⏳ Изображение поставлено в очередь\n\nПожалуйста, присылайте статистику текстом - это экономит и ваше время и время организаторов, исправляющих неточности распознавания. Возможно в будущем, парсинг статистики со скриншотов будет отключен",
       ua: "⏳ Зображення покладено в чергу\n\nБудь-ласка, надсилайте статистику текстом - це зберігае ваш час і час організаторів, що виправляють неточності розпізнавання. Можливо в майбутньому, статистика зі світлин не буде більше прийматися"
   },
   'Current language is "%s"':{
       ru: 'Текущий язык "%s"',
       ua: 'Використовується мова "%s"',
   },
   'Finish agent stats are welcome!': {
       ru: 'Принимаю финишные данные!',
       ua: 'Приймаю фінішні данні!',
   },
   'Start agent stats are welcome!': {
       ru: 'Принимаю стартовые данные!',
       ua: 'Приймаю стартові данні!'
   },
   'No more agent stats!':{
       ru: 'Прием игровой статистики завершен!',
       ua: 'Більше не приймаю статистику гравців!'
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
