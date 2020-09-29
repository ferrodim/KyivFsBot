const bot = require('./services/bot');
const {getUserLang, translate} = require('./services/lang');

module.exports = function (chatId, text, placeholders, formatted = false){
    let userLang = getUserLang(chatId);
    let translated = translate(text, userLang, placeholders);

    console.log('translated', translated);
    let options  = {};
    if (formatted){
        options.parse_mode = 'Markdown';
    }
    bot.sendMessage(chatId, translated, options);
};