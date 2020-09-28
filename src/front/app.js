const {mongo, rabbit, _} = require('flatground');
const APP_NAME = 'front';

const env = process.env;
const TelegramBot = require('node-telegram-bot-api');
const bot = new TelegramBot(env.TELEGRAM_TOKEN, {polling: {interval: 1000}});
const DEFAULT_CITY = 1;

Promise.all([
    mongo.configure({
        url: process.env.MONGO_URL
    }),
    rabbit.configure({
        url: process.env.RABBIT_URL,
    }),
]).then(async () => {
    await rabbit.bind(APP_NAME, ['call.telegramSend'], function(event) {
        if (event.event === 'call.telegramSend'){
            let args = event.args;
            let options  = {};
            if (args.formatted){
                options.parse_mode = 'Markdown';
            }
            bot.sendMessage(args.chatId, args.text, options);
        }
    });

    bot.on('message', async function(msg){
        //console.log('onMessage', msg);
    });

    const IMG_MIME_TYPES = ['image/png', 'image/jpg', 'image/jpeg'];
    async function proceedPhoto(msg){
        if (!msg.caption){
            sendTxt(msg.chat.id, _('Image must have a caption'));
            return;
        }
        if (!msg.caption.match(/^[a-zA-Z0-9_]+$/)){
            sendTxt(msg.chat.id, _('Image caption must be your nickname'));
            return;
        }
        await bot.forwardMessage(env.IMG_CHAT, msg.chat.id, msg.message_id);
        sendTxt(msg.chat.id, _('Image forwarded'));
    }

    bot.on('document', async function(msg){
        if (env.IMG_CHAT && IMG_MIME_TYPES.includes(msg.document.mime_type)){
            return proceedPhoto(msg);
        }
        sendTxt(msg.chat.id, _('Files are not allowed'));
    });

    bot.on('photo', async function(msg){
        if (msg.chat.id < 0){
            return;
        }

        if (env.IMG_CHAT){
            return proceedPhoto(msg);
        }

        sendTxt(msg.chat.id, _('Image parsing disabled'));
    });
    bot.on('text', async function(msg){
        /*if (msg.chat.id < 0){
            return;
        }*/

        let tgName = get_tg_nick(msg);

        let city = await mongo.collection('city').findOne({
                    cityId: DEFAULT_CITY,
                }, {
                    projection: {_id:0},
                }
            ) || {modes:[]};

        let event = {
            "event": 'core.messageIn',
            "text": msg.text,
            "msgid": msg.message_id,
            "chatid": msg.from.id,
            "rawMsg": msg,
            "tg_name": tgName,
            "isAdmin": await isAdmin(tgName),
            "cityId": city.cityId || DEFAULT_CITY,
            "city": city,
        };

        msg.isAdmin = event.isAdmin; // for legacy in module "bot"

        rabbit.emit(event);

        console.log('msg.text', msg.text);

        let isDummyRequest = msg.text[0] !== '/' && msg.text.length < 50 && !event.isAdmin;
        if (msg.text === '/ping'){
            sendTxt(msg.chat.id, _('Pong from %s'), ["front"]);
        } else if (msg.text === '/chatid'){
            sendTxt(msg.chat.id, _('Id of this chat is %s'), [msg.chat.id]);
        } else if (msg.text === '/start' || isDummyRequest){
            let startTime = city.startTime || 'not filled';
            let endTime = city.endTime || 'not filled';
            // let modes = city.modes || [];
            let template = _('Welcome, export me your start data at *%s*, and finish data at *%s*. Also use [google form](%s). Write /help for more info');
            sendTxt(msg.chat.id, template, [startTime, endTime, city.statUrl]);
        }
    });
}, err=>{
    console.error('Application "' + APP_NAME + '" could not start. Error: ', err);
});

async function isAdmin(tgName){
    if (process.env.SUPER_ADMIN === tgName){
        return true;
    } else {
        return !! await mongo.collection('admin').findOne({tgNick: tgName});
    }
}

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
            formatted: true,
        }
    };
    rabbit.emit(outcomeEvent);
}
