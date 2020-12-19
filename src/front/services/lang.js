const printf = require('printf');

const env = process.env;
const locales = ['ua', 'ru', 'en'];
const DEFAULT_LANG = env.DEFAULT_LANG || locales[0];
let db = {userLang: {}};

const fs = require('fs');
const Gettext = require('node-gettext');
const po = require('gettext-parser').po;

const gt = new Gettext();
locales.forEach((locale) => {
    const translationsContent = fs.readFileSync('/i18n/'+ locale + '.po', 'utf8');
    const parsedTranslations = po.parse(translationsContent);
    gt.addTranslations(locale, 'messages', parsedTranslations);
});


function getUserLang(chatId){
    return db.userLang[chatId] || DEFAULT_LANG;
}

function translate(text, lang, placeholders){
    if (!lang){
        lang = DEFAULT_LANG;
    }
    gt.setLocale(lang);
    text = gt.gettext(text);

    if (Array.isArray(placeholders)){
        text = printf(text, ...placeholders);
    }
    return text;
}

module.exports = {
    getUserLang, translate, db, locales
}