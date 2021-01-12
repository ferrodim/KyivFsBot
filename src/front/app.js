const {mongo, _} = require('flatground');
const bot = require('./services/bot');
const env = process.env;
const locales = ['ua', 'ru', 'en'];
const DEFAULT_LANG = env.DEFAULT_LANG || locales[0];
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

        let userResp = await mongo.collection('users').findOneAndUpdate({
            id: msg.from.id,
        }, {
            $set: {
                lastActive: Date.now(),
            },
            // $setOnInsert: {id: msg.from.id}
        }, {
            upsert: true,
            returnOriginal: false,
            projection: {_id: 0},
        });
        let user = userResp.value;

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
            user: user,
            userLang: user.language || DEFAULT_LANG,
        };

        let handler = await findCmdHandler(event);
        await handler(event);

        console.log('msg.text', msg.text);
    });
}, err=>{
    console.error('Application "front" could not start. Error: ', err);
});

let routes = {};
let questions = {};
const fs = require('fs');
fs.readdirSync('./handlers').forEach(fileName => {
    let chunks = fileName.match(/^cmd_(.+).js$/);
    if (chunks){
        let cmd = '/' + chunks[1];
        // console.log('found cmd '+ cmd);
        routes[cmd] = require('./handlers/' + fileName);
    }
});
fs.readdirSync('./handlers/txt').forEach(fileName => {
    let cmd = fileName.split('.')[0];
    routes[cmd] = require('./handlers/txt/' + fileName);
});
fs.readdirSync('./handlers/questions').forEach(fileName => {
    let cmd = fileName.split('.')[0];
    questions[cmd] = require('./handlers/questions/' + fileName);
});

async function findCmdHandler(event){
    if (event.user.question){
        await mongo('users').findOneAndUpdate({
            id: event.user.id,
        }, {
            $unset: {
                question: 1,
            },
        });
        return questions[event.user.question] || routes['welcome'];
    } else {
        let cmd = event.text.split(' ')[0];
        return routes[cmd] || routes['welcome'];
    }
}

async function isAdmin(tgName){
    if (process.env.SUPER_ADMIN === tgName){
        return true;
    } else {
        return !! await mongo.collection('admin').findOne({tgNick: tgName});
    }
}
