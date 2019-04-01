#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
from functools import wraps
import telebot
import json
import random
import string
import io
import re
from config import ADMINS, MODES, API_TOKEN, WELCOME, CHAT_OK, CHAT_FAIL
from image_process import parse_image

print("restart")

bot = telebot.TeleBot(API_TOKEN)
try:
    datafile = open("base.txt", "r")
    data = json.load(datafile)
except FileNotFoundError:
    data = {}
    datafile = open("base.txt", "w")
    json.dump(data, datafile, ensure_ascii=False)
if "welcome" not in data.keys():
    data["welcome"] = WELCOME
if "getStart" not in data.keys():
    data["getStart"] = False
if "getEnd" not in data.keys():
    data["getEnd"] = False
if "okChat" not in data.keys():
    data["okChat"] = CHAT_OK
if "failChat" not in data.keys():
    data["failChat"] = CHAT_FAIL
if "counters" not in data.keys():
    data["counters"] = {}
datafile.close()
datafile = open("base.txt", "w")
json.dump(data, datafile, ensure_ascii=False)
datafile.close()


def save_data():
    data_file = open("base.txt", "w")
    json.dump(data, data_file, ensure_ascii=False)
    data_file.close()


def restricted(func):
    @wraps(func)
    def wrapped(message, *args, **kwargs):
        if message.from_user.username not in ADMINS:
            bot.reply_to(message, "А ну кыш отсюда!")
            return
        return func(message, *args, **kwargs)
    return wrapped


@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.reply_to(message, (data["welcome"]))


@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.reply_to(message, "username - (for admins) Get userinfo\n"
                          "/startevent - (for admins) Begin taking start screenshots\n"
                          "/endevent - (for admins) Begin taking final screenshots\n"
                          "/reset - (for admins) Clear all data and settings\n"
                          "/result - (for admins) Get result table file\n"
                          "/stop - (for admins) Stop taking events\n"
                          "/setwelcome - (for admins) Set welcome message")


@bot.message_handler(commands=["setwelcome"])
@restricted
def cmd_setwelcome(message):
    data["welcome"] = message.text[str(message.text + " ").find(" "):]
    save_data()
    bot.send_message(message.chat.id, "Обновил приветствие")


@bot.message_handler(commands=["chatid"])
@restricted
def cmd_chatid(message):
    bot.send_message(message.chat.id, "Айди этого чата: %s" % message.chat.id)


@bot.message_handler(commands=["set"])
@restricted
def cmd_set(message):
    allowed_modes = ["AP", "Level"] + MODES
    chunks = message.text.replace("@", "").replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) == 4 and chunks[2] == 'Nick') or \
                     (len(chunks) == 5 and chunks[2] in ["start", "end"] and chunks[3] in allowed_modes)
    if not is_valid_query:
        bot.send_message(message.chat.id, ("Неверный формат запроса. Нужно писать:\n"
                                           "`/set telegram_nick start Param value`\n"
                                           "`/set telegram_nick end Param value`\n"
                                           "`/set telegram_nick Nick game_nick`"), parse_mode="Markdown")
        return
    agentname = chunks[1]
    if agentname not in data["counters"].keys():
        data["counters"][agentname] = {"start": {}, "end": {}}
    if chunks[2] == 'Nick':
        counter = chunks[2]
        value = chunks[3]
        data["counters"][agentname][counter] = value
    else:
        step = chunks[2]
        counter = chunks[3]
        value = int(chunks[4])
        data["counters"][agentname][step][counter] = value
    save_data()
    txt = "Досье на: @%s\n" % agentname
    txt += user_info(agentname)
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")


@bot.message_handler(commands=["reset"])
@restricted
def cmd_reset(message):
    data.clear()
    data["getStart"] = False
    data["getEnd"] = False
    data["okChat"] = CHAT_OK
    data["failChat"] = CHAT_FAIL
    data["counters"] = {}
    data["welcome"] = WELCOME
    save_data()
    bot.reply_to(message, "База данных очищена")


@bot.message_handler(commands=["startevent"])
@restricted
def cmd_startevent(message):
    data["getStart"] = True
    data["getEnd"] = False
    save_data()
    bot.send_message(message.chat.id, "Принимаю стартовые скрины!")


@bot.message_handler(commands=["endevent"])
@restricted
def cmd_endevent(message):
    data["getStart"] = False
    data["getEnd"] = True
    save_data()
    bot.send_message(message.chat.id, "Принимаю финишные скрины!")


@bot.message_handler(commands=["stop"])
@restricted
def cmd_stop(message):
    data["getStart"] = False
    data["getEnd"] = False
    save_data()
    bot.send_message(message.chat.id, "Не принимаю скрины!")


@bot.message_handler(commands=["result"])
@restricted
def cmd_result(message):
    delimiter = message.text[len("/result "):len("/result ")+1]
    if delimiter == '':
        delimiter = ','
    txt = "TG_nick;Game_nick"
    allowed_modes = ["AP", "Level"] + MODES
    for mode in allowed_modes:
        txt += ";Start_%s;End_%s" % (mode, mode)
    txt += "\n"
    for agentname in data["counters"].keys():
        agentdata = {"start": {}, "end": {}, "Nick": data["counters"][agentname].get("Nick", "-")}
        for mode in allowed_modes:
            agentdata["start"][mode] = "-"
            agentdata["end"][mode] = "-"
        if "start" in data["counters"][agentname].keys():
            agentdata["start"].update(data["counters"][agentname]["start"])
        if "end" in data["counters"][agentname].keys():
            agentdata["end"].update(data["counters"][agentname]["end"])
        txt += '"%s";"%s";%s;%s;%s;%s' % (agentname, agentdata["Nick"], agentdata["start"]["Level"], agentdata["end"]["Level"], agentdata["start"]["AP"], agentdata["end"]["AP"])
        for mode in MODES:
            txt += ";%s;%s" % (agentdata["start"][mode], agentdata["end"][mode])
        txt += "\n"
    txt = txt.replace(';', delimiter)
    resultfile = open("result.csv", "w")
    resultfile.write(txt)
    resultfile.close()
    resultfile = open("result.csv", "rb")
    bot.send_document(message.chat.id, resultfile)
    resultfile.close()


@bot.message_handler(commands=["me"])
def cmd_me(message):
    txt = user_info(message.from_user.username)
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")


@bot.message_handler(commands=["clearme"])
def cmd_clearme(message):
    if message.from_user.username in data["counters"].keys():
        del data["counters"][message.from_user.username]
        save_data()
        bot.reply_to(message, "Ваши данные удалены")
    else:
        bot.reply_to(message, "Бот не располагает данными на вас")


@bot.message_handler(commands=["nick"])
def cmd_nick(message):
    chunks = message.text.replace("@", "").replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) == 2 and re.fullmatch(r'[a-zA-Z0-9\-_]+', chunks[1]))
    if not is_valid_query:
        bot.send_message(message.chat.id, ("Неверный формат запроса. Нужно писать:\n"
                                           "`/nick my_game_nick`\n"), parse_mode="Markdown")
        return
    tg_name = get_tg_nick(message)
    game_nick = chunks[1]
    if tg_name not in data["counters"].keys():
        data["counters"][tg_name] = {"start": {}, "end": {}}
    data["counters"][tg_name]['Nick'] = game_nick
    save_data()
    txt = "Досье на: @%s\n" % tg_name
    txt += user_info(tg_name)
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")


def user_info(username):
    allowed_modes = ["AP", "Level"] + MODES
    if not username in data["counters"].keys():
        return 'Бот ничего не знает по вам'
    user_data = data["counters"][username]
    txt = ""
    game_nick = user_data.get("Nick", "-")
    if game_nick != '-' and game_nick !=  username:
        txt = "Ник в игре: %s\n" % game_nick
    txt += "== Стартовые показатели:"
    for mode in allowed_modes:
        value = user_data["start"].get(mode, "-")
        txt += "\n_%s:_ *%s*" % (mode, value)
    if "end" in user_data.keys() and len(user_data['end'].keys()) > 0:
        txt += "\n== Финишные показатели:"
        for mode in allowed_modes:
            value = user_data["end"].get(mode, "-")
            txt += "\n_%s_: *%s*" % (mode, value)
            if mode in user_data["start"].keys() and mode in user_data["end"].keys():
                delta = (user_data["end"][mode] - user_data["start"][mode])
                txt += " (+%s)" % delta
    return txt


def get_tg_nick(message):
    tg_nick = message.chat.username
    if (tg_nick == None):
        tg_nick = str(message.chat.id)
    return tg_nick


@bot.message_handler(func=lambda message: True, content_types=["text"])
def process_msg(message):
    if message.chat.username in ADMINS:
        user_tg_name = message.text.replace('@', '')
        if user_tg_name in data["counters"].keys():
            txt = "Досье на: @%s\n" % user_tg_name
            txt += user_info(user_tg_name)
        else:
            txt = "Такой пользователь не найден в базе"
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")
    else:
        bot.reply_to(message, (data["welcome"]), parse_mode="Markdown")


@bot.message_handler(func=lambda message: True, content_types=["photo"])
def process_photo(message):
    agentname = get_tg_nick(message)
    if message.forward_from:
        if (message.chat.username in ADMINS) or (message.chat.username == message.forward_from.username):
            agentname = message.forward_from.username
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    f = io.BytesIO(downloaded_file)
    f.seek(0)
    img = Image.open(f)
    filename = "Screens/" + agentname + "_"
    if data["getStart"]:
        datakey = "start"
    elif data["getEnd"]:
        datakey = "end"
    else:
        datakey = "pre"
    postfix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    filename += datakey + "_" + str(postfix) + ".jpg"
    with open(filename, "wb") as new_file:
        new_file.write(downloaded_file)
    parseResult = parse_image(img)
    if not data["getStart"] and not data["getEnd"]:
        txt = "Регистрация на эвент ещё не началась. На твоём изображении я вижу вот что:\n\n"
        if parseResult["success"]:
            txt += "Агент {},\nAP {:,},\nLvl {},\n{} {:,}".format(agentname, parseResult["AP"], parseResult["Level"], parseResult["mode"], parseResult[parseResult["mode"]])
        else:
            txt += "Данные с изображения распарсить не удалось"
        bot.send_message(message.chat.id, (txt))
        return
    if parseResult["success"]:
        if agentname not in data["counters"].keys():
            data["counters"][agentname] = {"pre":{}, "start": {}, "end": {}}
        data["counters"][agentname][datakey].update(parseResult)
        save_data()
        bot.reply_to(message, ("Изображение распознано. Проверьте правильность цифр:\n%s"%(user_info(agentname))), parse_mode="Markdown")
        if data["okChat"]:
            bot.forward_message(data["okChat"], message.chat.id, message.message_id)
            bot.send_message(data["okChat"], "Агент {}, AP {:,}, {} {:,}".format(agentname, parseResult["AP"], parseResult["mode"], parseResult[parseResult["mode"]]))
    else:
        bot.reply_to(message, "Не могу разобрать скрин! Отправьте другой, или зарегистрируйтесь у оргов вручную")
        if data["failChat"] != 0:
            bot.forward_message(data["failChat"], message.chat.id, message.message_id)


if __name__ == "__main__":
    bot.polling(none_stop=True)
