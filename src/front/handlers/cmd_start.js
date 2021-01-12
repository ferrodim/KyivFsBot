const {_, translate, bot} = require('../core');

module.exports = async function (event){
    let city = event.city;
    let fsName = city.fsName || '< FS NAME >'; // Like Kyiv - August 2020
    let startTime = city.startTime || '??';
    let endTime = city.endTime || '??';
    let text = _('Welcome to %s, export me your start data at *%s*, and finish data at *%s*. Also use [google form](%s). Write /help for more info');

    if (event.chatid < 0){
        return; // ignore txt messages in chat groups
    }

    let msg = translate(text, event.userLang, [fsName, startTime, endTime, city.statUrl]);
    await bot.sendMessage(event.chatid, msg, {
        parse_mode: 'Markdown',
        reply_markup: JSON.stringify({
            keyboard: [
                ['Register'],
                ['Profile'],
                ['About_bot']
            ]
        })
    });
};