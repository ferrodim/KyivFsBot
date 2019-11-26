const {mongo, rabbit, _} = require('../shared/framework');
const APP_NAME = 'front';

const TelegramBot = require('node-telegram-bot-api');
const bot = new TelegramBot(process.env.TELEGRAM_TOKEN, {polling: {interval: 1000}});
const DEFAULT_CITY = 1;

Promise.all([
    mongo.configure({
        url: process.env.MONGO_URL
    }),
    rabbit.configure({
        url: process.env.RABBIT_URL,
    }),
]).then(async () => {
    await rabbit.bind(APP_NAME, 'call.telegramSend', function(event) {
        if (event.event === 'call.telegramSend'){
            let args = event.args;
            bot.sendMessage(args.chatId, args.text);
        }
    });
    bot.on('message', async function(msg){
        if (msg.chat.id < 0){
            return;
        }

        let tgName = get_tg_nick(msg);
        msg.isAdmin = !! await mongo.collection('admin').findOne({tgNick: tgName});
        let city = await mongo.collection('city').findOne({
                    cityId: DEFAULT_CITY,
                }, {
                    projection: {_id:0},
                }
            ) || {};

        rabbit.emit({
            "event": 'core.messageIn',
            "text": msg.text,
            "msgid": msg.message_id,
            "chatid": msg.from.id,
            "rawMsg": msg,
            "tg_name": tgName,
            "cityId": city.cityId,
        });

        console.log('msg.text', msg.text);

        if (msg.text === '/ping'){
            sendTxt(msg.chat.id, _('Pong from %s'), ["front"]);
        } else if (msg.text === '/start'){
            let startTime = city.startTime || 'not filled';
            let endTime = city.endTime || 'not filled';
            let modes = city.modes || [];
            let template = _('Welcome, export me your start data at *%s*, and finish data at *%s*. Active modes *%s*. Write /help for more info');
            sendTxt(msg.chat.id, template, [startTime, endTime, modes.join()]);
        }
    });
}, err=>{
    console.error('Application "' + APP_NAME + '" could not start. Error: ', err);
});

function get_tg_nick(msg){
    return msg.from.username || ('#' + msg.from.id);
}

function sendTxt(chatId, text, placeholders){
    let outcomeEvent = {
        event: 'call.translateAndSend',
        args: {
            chatId: chatId,
            text: text,
            placeholders:  placeholders || [],
        }
    };
    rabbit.emit(outcomeEvent);
}
