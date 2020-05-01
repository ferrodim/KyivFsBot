const {_} = require('flatground');
const sendText = require('../sendText');

module.exports = async function (event){
    if (!event.isAdmin){
        return;
    }
    let txt = "/admin_list - Admin list \n";
    txt += "/admin_add <tgnick> - Add admin \n";
    txt += "/admin_remove <tgnick> - Remove admin\n";
    txt += "/city_start_time <time> - Used inside welcome notification\n";
    txt += "/city_end_time <time> - Used inside welcome notification\n";
    txt += "/city_stat_url <url> - Full url for Autoscore google-table\n";
    txt += "/modes_list - Configure modes for /me, /result \n";
    txt += "/modes_add <mode> - Configure modes for /me, /result \n";
    txt += "/modes_remove <mode> - Configure modes for /me, /result\n";
    sendText(event.chatid, txt);
};