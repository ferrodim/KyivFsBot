const env = process.env;
let connect = require('amqplib').connect(env.RABBIT_URL);
let queueName = 'translator';
let db = {userLang: {}};


const fs = require('fs');
const Gettext = require('node-gettext');
const po = require('gettext-parser').po;
const printf = require('printf');
const locales = ['ua', 'ru', 'en'];
const DEFAULT_LANG = env.DEFAULT_LANG || locales[0];
const gt = new Gettext();

locales.forEach((locale) => {
    const translationsContent = fs.readFileSync('/i18n/'+ locale + '.po', 'utf8');
    const parsedTranslations = po.parse(translationsContent);
    gt.addTranslations(locale, 'messages', parsedTranslations);
});

connect.then(con => {
    console.log('connection ready');
    return con.createChannel();
}).then(async ch => {
    await ch.assertQueue(queueName);
    await ch.bindQueue(queueName, 'topic', 'core.messageIn');
    ch.consume(queueName, function(msg) {
        try {
            if (msg !== null) {
                let event = JSON.parse(msg.content.toString());
                console.log('{Rabbit} <= ' + JSON.stringify(event));
                if (event.event === 'core.messageIn'){
                    if (!event.text){
                        return;
                    }
                } else {
                    console.log('unknown event', event);
                }
            }
        } catch (e){
        } finally {
            ch.ack(msg);
        }
    });
});

function getUserLang(chatId){
    return db.userLang[chatId] || DEFAULT_LANG;
}

function sendTxt(ch, chatId, text, placeholders, formatted){
    let userLang = getUserLang(chatId);
    let outcomeEvent = {
        event: 'call.telegramSend',
        args: {
            chatId: chatId,
            text: translate(text, userLang, placeholders),
            formatted: !!formatted
        }
    };
    let outStr = JSON.stringify(outcomeEvent);
    console.log('{Rabbit} => ' + outStr);
    ch.publish('topic', outcomeEvent.event, Buffer.from(outStr, 'utf8'));
}

function translate(text, lang, placeholders){
    if (!lang){
        lang = DEFAULT_LANG;
    }
    gt.setLocale(lang);
    text = gt.gettext(text);

    if (Array.isArray(placeholders)){
        text = printf(text, ...placeholders);
    }
    return text;
}

function _(msg){
    return msg;
}
