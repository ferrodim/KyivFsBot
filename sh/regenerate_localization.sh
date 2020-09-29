xgettext -o i18n/messages.pot --no-location --from-code utf-8 src/*/*.js
msgmerge -U i18n/en.po i18n/messages.pot --backup=off
msgmerge -U i18n/ua.po i18n/messages.pot --backup=off
msgmerge -U i18n/ru.po i18n/messages.pot --backup=off
rm -f i18n/*.mo