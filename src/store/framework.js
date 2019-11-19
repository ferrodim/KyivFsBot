
function MongoService(){
    this._db = null;
    this.ready = new Promise((accept, reject) =>  {
        this.configure = function(args){
            require('mongodb').MongoClient.connect(args.url, {useUnifiedTopology: true}, (err, client) => {
                console.log("Connected successfully to db server");
                this._db = client.db();
                accept();
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
    await this.channel.bindQueue(queueName, 'topic', routeKey);
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

module.exports = {
    mongo: new MongoService(),
    rabbit: new RabbitService(),
    _:_=>_,
};