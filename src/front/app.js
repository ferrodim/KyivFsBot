const {mongo, _} = require('flatground');
const APP_NAME = 'front';

const env = process.env;
const bot = require('./services/bot');
const DEFAULT_CITY = 1;

Promise.all([
    mongo.configure({
        url: env.MONGO_URL
    }),
]).then(async () => {
    // bot.on('message', async function(msg){//console.log('onMessage', msg);});
    bot.on('document', require('./handlers/bot_document'));
    bot.on('photo', require('./handlers/bot_photo'));
    bot.on('text', async function(msg){
        /*if (msg.chat.id < 0){
            return;
        }*/

        let tgName = msg.from.username || ('#' + msg.from.id);

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
            "chatid": msg.chat.id,
            //'fromId': msg.from.id,
            "rawMsg": msg,
            "tg_name": tgName,
            "isAdmin": await isAdmin(tgName),
            "cityId": city.cityId || DEFAULT_CITY,
            "city": city,
        };

        let handler = findCmdHandler(event);
        await handler(event);

        console.log('msg.text', msg.text);
    });
}, err=>{
    console.error('Application "' + APP_NAME + '" could not start. Error: ', err);
});

function findCmdHandler(event){
    let cmd = event.text.split(' ')[0];
    switch (cmd){
        case '/admin_add': return require('./handlers/cmd_admin_add');
        case '/admin_list': return require('./handlers/cmd_admin_list');
        case '/admin_remove': return require('./handlers/cmd_admin_remove');

        case '/city_start_time': return require('./handlers/cmd_city_start_time');
        case '/city_end_time': return require('./handlers/cmd_city_end_time');
        case '/city_stat_url': return require('./handlers/cmd_city_stats_url');

        case '/ping': return require('./handlers/cmd_ping');
        case '/chatid': return require('./handlers/cmd_chatid');
        case '/start': return require('./handlers/cmd_start');
        case '/lang': return require('./handlers/cmd_lang');
        case '/langlist': return require('./handlers/cmd_langlist');

        case '/help': return require('./handlers/cmd_help');
        default: return require('./handlers/cmd_start');
    }

}

async function isAdmin(tgName){
    if (process.env.SUPER_ADMIN === tgName){
        return true;
    } else {
        return !! await mongo.collection('admin').findOne({tgNick: tgName});
    }
}
