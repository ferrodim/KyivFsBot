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




