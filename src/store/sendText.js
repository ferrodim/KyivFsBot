const {rabbit} = require('../shared/framework');

module.exports = function (chatId, text, placeholders){
    let outcomeEvent = {
        event: 'call.translateAndSend',
        args: {
            chatId: chatId,
            text: text,
            placeholders:  placeholders || [],
        }
    };
    rabbit.emit(outcomeEvent);
};
