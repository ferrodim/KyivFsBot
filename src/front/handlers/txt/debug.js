const {bot} = require('../../core');
const JSON5 = require('json5');

module.exports = async function (e){
    if (e.chatid < 0){
        return; // ignore txt messages in chat groups
    }

    let msg = JSON5.stringify(e, null, 4);

    await bot.sendMessage(e.chatid, msg, {
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