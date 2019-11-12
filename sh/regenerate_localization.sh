xgettext -o i18n/messages.pot --from-code utf-8 src/bot/bot.py src/decoder/decoder.py src/translator/app.js
msgmerge -U i18n/en.po i18n/messages.pot --backup=off
msgmerge -U i18n/ua.po i18n/messages.pot --backup=off
msgmerge -U i18n/ru.po i18n/messages.pot --backup=off