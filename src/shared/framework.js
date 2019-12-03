
const CONNECT_TIMEOUT = 5000;

function MongoService(){
    this._db = null;
    this.ready = new Promise((accept, reject) =>  {
        this.configure = async function(args){
            let connect_timer = setTimeout(()=>{
                reject("Mongo connection timeout, after " + CONNECT_TIMEOUT + 'ms wait');
            }, CONNECT_TIMEOUT);

            require('mongodb').MongoClient
                .connect(args.url, {useUnifiedTopology: true})
                .then(client => {
                    clearTimeout(connect_timer);
                    console.log("Connected successfully to db server");
                    this._db = client.db();
                    accept();
                }, err => {
                    clearTimeout(connect_timer);
                    reject(err);
                });

            return this.ready;
        };
    });
}

MongoService.prototype.collection = function(name){
    return this._db.collection(name);
};

function RabbitService(){
    this.channel = null;
    this.ready = new Promise((accept, reject) =>  {
        this.configure = async function(args){
            let connect = await require('amqplib').connect(args.url);
            this.channel = await connect.createChannel();
            accept();
            return this.ready;
        };
    });
}

RabbitService.prototype.bind = async function(queueName, routeKey, callback){
    await this.channel.assertQueue(queueName);
    if (Array.isArray(routeKey)){
        for (let route of routeKey){
            await this.channel.bindQueue(queueName, 'topic', route);
        }
    } else {
        await this.channel.bindQueue(queueName, 'topic', routeKey);
    }

    this.channel.consume(queueName, async msg => {
        if (msg){
            let event = JSON.parse(msg.content.toString());
            console.log('{Rabbit} <= ' + JSON.stringify(event));
            await callback(event);
        }
        this.channel.ack(msg);
    });
};

RabbitService.prototype.emit = function(event){
    let outStr = JSON.stringify(event);
    console.log('{Rabbit} => ' + outStr);
    this.channel.publish('topic', event.event, Buffer.from(outStr, 'utf8'));
};

// const TelegramBot = require('node-telegram-bot-api');
// const bot = new TelegramBot(process.env.TELEGRAM_TOKEN, {polling: {interval: 1000}});

module.exports = {
    mongo: new MongoService(),
    rabbit: new RabbitService(),
    _:_=>_,
};