With friendship with: https://github.com/DreidSpb/FsSpbBot

Manual installation
-----------------------------------
* register you own telegramm bot via https://telegram.me/botfather and save Token for future use (API_TOKEN)
* download the sources
* copy config.sample.py -> config.py
* inside config.py fill API_TOKEN - value, obtained from BotFather
* inside config.py fill ADMINS - telegram nicks of users, that can manage bot
* inside config.py fill MODES - what screens you bot will count (Trekker/Builder/Purifier is default. Change if you wish)
* inside config.py fill WELCOME - new users will see it, on conversation start
* start your bot by "docker-compose up -d" (it will take nearly 10 minutes)
* create two telegram chats (Supergroups is better), and add your new bot to them. First group for good screens, and second - for bad screens
* write "/chatid" in them, and detect its ID
* edit your config.py one more time and:
* inside config.py fill CHAT_OK - id of chat, where bot will forward good screens
* inside config.py fill CHAT_FAIL - id of chat, where bot will forward bad screens (that it cant to recognize)
* restart bot with "docker-compose restart"
* test you bot with /help or /me command. Or send some screenshots to it


Fast install for Ubuntu 18.04 (if you already have config file)
-----------------------------------
* sudo -s
* curl -s https://raw.githubusercontent.com/ferrodim/KyivFsBot/master/sh/autoinstall.sh | bash -s --
* ... fill the config.py with your parameters ...
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
