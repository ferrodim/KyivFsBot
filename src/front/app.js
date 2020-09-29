const {mongo, _} = require('flatground');
const APP_NAME = 'front';

const env = process.env;
const bot = require('./services/bot');
const DEFAULT_CITY = 1;

// translator init
const {getUserLang, translate, db, locales} = require('./services/lang');

function botSend(args){
    let options  = {};
    if (args.formatted){
        options.parse_mode = 'Markdown';
    }
    bot.sendMessage(args.chatId, args.text, options);
}

Promise.all([
    mongo.configure({
        url: process.env.MONGO_URL
    }),
]).then(async () => {
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

        let cmd = event.text.split(' ')[0];
        findCmdHandler(cmd)(event);

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
        if (msg.text === '/lang'){
            sendTxt(msg.chat.id, _('Current language is "%s"'), [getUserLang(event.chatid)]);
        }
        if (msg.text === '/langlist'){
            sendTxt(msg.chat.id, _('List of languages: %s'), [locales.join()]);
        }
        if (msg.text.indexOf('/lang ') === 0){
            let newLang = msg.text.split(' ')[1];
            if (locales.includes(newLang)){
                db.userLang[msg.chat.id] = newLang;
                sendTxt(msg.chat.id, _('Language changed to "%s"'), [newLang]);
            } else {
                sendTxt(msg.chat.id, _('Unknown language "%s"'), [newLang]);
            }
        }
    });
}, err=>{
    console.error('Application "' + APP_NAME + '" could not start. Error: ', err);
});

function findCmdHandler(cmd){
    switch (cmd){
        case '/admin_add': return require('./handlers/cmd_admin_add');
        case '/admin_list': return require('./handlers/cmd_admin_list');
        case '/admin_remove': return require('./handlers/cmd_admin_remove');

        case '/city_start_time': return require('./handlers/cmd_city_start_time');
        case '/city_end_time': return require('./handlers/cmd_city_end_time');
        case '/city_stat_url': return require('./handlers/cmd_city_stats_url');

        case '/help': return require('./handlers/cmd_help');
        default: return function(){};
    }
}

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
    sendTxt2(chatId, text, placeholders || [], true);
}

function sendTxt2(chatId, text, placeholders, formatted){
    let userLang = getUserLang(chatId);
    botSend({
        chatId: chatId,
        text: translate(text, userLang, placeholders),
        formatted: !!formatted
    });
}




