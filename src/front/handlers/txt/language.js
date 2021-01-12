const {_, translate, bot, locales, mongo} = require('../../core');

module.exports = async function (e){
    let text = _('Choose language');
    let keyboard = [locales, ['back']];

    if (e.chatid < 0){
        return; // ignore txt messages in chat groups
    }

    let msg = translate(text, e.userLang, []);

    await mongo('users').findOneAndUpdate({
        id: e.user.id,
    }, {
        $set: {
            question: 'chooseLanguage',
        },
    });

    await bot.sendMessage(e.chatid, msg, {
        parse_mode: 'Markdown',
        reply_markup: JSON.stringify({
            keyboard,
        })
    });
};