With friendship with:
* https://github.com/DreidSpb/FsSpbBot
* https://github.com/john1123/FirstSaturdayBot

Manual installation
-----------------------------------
* register you own telegramm bot via https://telegram.me/botfather and save Token for future use (API_TOKEN)
* download the sources
* copy sample.env -> .env
* inside .env fill TELEGRAM_TOKEN - value, obtained from BotFather
* inside .env fill SUPER_ADMIN - your telegram nick
* start your bot by "docker-compose up -d" (it will take nearly 10 minutes)
* restart bot with "docker-compose restart"
* test you bot with /help or /me command. Or send some screenshots to it


Fast install for Ubuntu 18.04 (if you already have config file)
-----------------------------------
* sudo -s
* curl -s https://raw.githubusercontent.com/ferrodim/KyivFsBot/master/sh/autoinstall.sh | bash -s --
* ... fill the .env with your parameters ...
* docker-compose up -d
* ... wait ~10 minutes, while docker install all dependencies ...


Main differences with DreidSpb/FsSpbBot
-----------------------------------
* better installation docs
* faster installation
* docker + rabbit added
* commands like /me, /clearme for GDPR compliance
* user can send any count of screens. New screens will overwrite older
* bot will recognise users screens even before event start or after event end
* bot will notify user, when users data changes
* debug instruments removed
* no full profile-images
* no modes, that have never been used on Kyiv FS
* no internal sheduler for automatic start/end event
* no broadcasts - admin can't send message to all user by /sendAll command
* admins can change users data manually by /set command
* bot automatically use all available CPU cores
