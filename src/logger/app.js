let connect = require('amqplib').connect(process.env.RABBIT_URL);
let queueName = 'logger';

connect.then(con => {
    console.log('connection ready');
    return con.createChannel();
}).then(ch => {
    return ch.assertQueue(queueName).then(function(ok) {
        return ch.consume(queueName, function(msg) {
            if (msg !== null) {
                console.log(msg.content.toString());
                ch.ack(msg);
            }
        });
    });
});

console.log('logger init');

setInterval(() => {
    console.log('logger online!');
}, 5000)