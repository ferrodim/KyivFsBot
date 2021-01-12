const {_, translate, bot} = require('../../core');

module.exports = async function (event){
    let text = _('Welcome to FS bot');

    if (event.chatid < 0){
        return; // ignore txt messages in chat groups
    }

    let msg = translate(text, event.userLang, []);

    await bot.sendMessage(event.chatid, msg, {
        parse_mode: 'Markdown',
        reply_markup: JSON.stringify({
            keyboard: [
                ['language'],
                ['register'],
                ['rules'],
            ]
        })
    });
};