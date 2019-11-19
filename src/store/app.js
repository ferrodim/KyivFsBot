const {mongo, rabbit} = require('./framework');
const APP_NAME = 'store';

Promise.all([
    mongo.configure({
        url: process.env.MONGO_URL
    }),
    rabbit.configure({
        url: process.env.RABBIT_URL,
    }),
]).then(async () => {
    await rabbit.bind(APP_NAME, 'core.messageIn', function(event) {
        findCmdHandler(event.text)(event);
    });
}, err=>{
    console.error('Application "' + APP_NAME + '" could not start. Error: ', err);
});

function findCmdHandler(cmd){
    switch (cmd){
        case '/store_info': return require('./handlers/cmd_store_info');
        case '/store_increment': return require('./handlers/cmd_store_increment');
        case '/store_read': return require('./handlers/cmd_store_read');
        case '/ping': return require('./handlers/cmd_ping');
        default: return function(){};
    }
}


