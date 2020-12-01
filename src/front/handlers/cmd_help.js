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
    txt += "/city_fs_name <name> - FS name, e.g. 'Kyiv - August 2020'\n";
    sendText(event.chatid, txt);
};