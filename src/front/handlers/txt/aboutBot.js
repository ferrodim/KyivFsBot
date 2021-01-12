const {_, translate, bot} = require('../../core');

module.exports = async function (event){
    let text = _('This bot was created by @ferrodim');

    if (event.chatid < 0){
        return; // ignore txt messages in chat groups
    }

    let msg = translate(text, event.userLang, []);
    await bot.sendMessage(event.chatid, msg, {
        parse_mode: 'Markdown',
        reply_markup: JSON.stringify({
            keyboard: [
                ['Register2'],
                ['Profile2'],
                ['About bot2']
            ]
        })
    });
};