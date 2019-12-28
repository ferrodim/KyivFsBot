const {mongo, rabbit} = require('flatground');
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
        let cmd = event.text.split(' ')[0];
        console.log('cmd', cmd);
        findCmdHandler(cmd)(event);
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
        case '/admin_add': return require('./handlers/cmd_admin_add');
        case '/admin_list': return require('./handlers/cmd_admin_list');
        case '/admin_remove': return require('./handlers/cmd_admin_remove');
        case '/modes_add': return require('./handlers/cmd_modes_add');
        case '/modes_list': return require('./handlers/cmd_modes_list');
        case '/modes_remove': return require('./handlers/cmd_modes_remove');
        case '/city_start_time': return require('./handlers/cmd_city_start_time');
        case '/city_end_time': return require('./handlers/cmd_city_end_time');
        default: return function(){};
    }
}


