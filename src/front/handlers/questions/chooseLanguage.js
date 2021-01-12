const sendText = require('../../sendText');
const {_, translate, bot, locales, mongo} = require('../../core');
const welcomeHandler = require('../txt/welcome');

module.exports = async function (e){
    let newLang = e.text;
    if (locales.includes(newLang)) {
        await mongo('users').findOneAndUpdate({
            id: e.user.id,
        }, {
            $set: {
                language: newLang,
            },
        });

        let msg = translate(_('Language changed to "%s"'), e.userLang, [newLang]);
        // TODO internal redirects
        await bot.sendMessage(e.chatid, msg, {
            parse_mode: 'Markdown',
        });
        welcomeHandler(e);
    } else if (newLang === 'back') {
        welcomeHandler(e);
    } else {
        sendText(e.chatid, _('Unknown language "%s"'), [newLang]);
    }
};