let connect = require('amqplib').connect(process.env.RABBIT_URL);
let queueName = 'translator';
let db = {userLang: {}};

const fs = require('fs');
const Gettext = require('node-gettext');
const po = require('gettext-parser').po;
const locales = ['en', 'ru', 'ua'];
const DEFAULT_LANG = locales[0];
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
    await ch.bindQueue(queueName, 'topic', 'call.translateAndSend');
    await ch.bindQueue(queueName, 'topic', 'call.setLang');
    await ch.bindQueue(queueName, 'topic', 'core.messageIn');
    ch.consume(queueName, function(msg) {
        if (msg !== null) {
            let event = JSON.parse(msg.content.toString());
            console.log('{Rabbit} <= ' + JSON.stringify(event));
            if (event.event === 'call.translateAndSend'){
                sendTxt(ch, event.args.chatId, event.args.text, event.args.placeholders, event.args.formatted);
            } else if (event.event === 'core.messageIn'){
                if (event.text === '/lang'){
                    sendTxt(ch, event.chatid, _('Current language is "%s"'), [getUserLang(event.chatid)]);
                }
                if (event.text === '/ping'){
                    sendTxt(ch, event.chatid, _('Pong from %s'), ["translator"]);
                }
                if (event.text === '/langlist'){
                    sendTxt(ch, event.chatid, _('List of languages: %s'), [locales.join()]);
                }
                if (event.text.indexOf('/lang ') === 0){
                    let newLang = event.text.split(' ')[1];
                    if (locales.includes(newLang)){
                        db.userLang[event.chatid] = newLang;
                        sendTxt(ch, event.chatid, _('Language changed to "%s"'), [newLang]);
                    } else {
                        sendTxt(ch, event.chatid, _('Unknown language "%s"'), [newLang]);
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
        for (let placeholder of placeholders){
            text = text.replace('%s', placeholder);
        }
    }
    return text;
}

function _(msg){
    return msg;
}
