#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
from functools import wraps
import telebot
import json
import datetime
import re
import random
import string
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
if not "welcome" in data.keys():
    data["welcome"] = WELCOME
if not "getStart" in data.keys():
    data["getStart"] = False
if not "getEnd" in data.keys():
    data["getEnd"] = False
if not "okChat" in data.keys(): 
    data["okChat"] = CHAT_OK
if not "failChat" in data.keys():
    data["failChat"] = CHAT_FAIL
if not "counters" in data.keys():
    data["counters"] = {}
datafile.close()
datafile = open("base.txt", "w")
json.dump(data, datafile, ensure_ascii=False)
datafile.close()


def save_data():
    datafile = open("base.txt", "w")
    json.dump(data, datafile, ensure_ascii=False)
    datafile.close()











def restricted(func):
    @wraps(func)
    def wrapped(message, *args, **kwargs):
        if message.from_user.username not in ADMINS:
            bot.reply_to(message, ("А ну кыш отсюда!"))
            return
        return func(message, *args, **kwargs)
    return wrapped


@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.reply_to(message, (data["welcome"]))


@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.reply_to(message, ("username - (for admins) Get userinfo\n/startevent - (for admins) Begin taking start screenshots\n/endevent - (for admins) Begin taking final screenshots\n/reset - (for admins) Clear all data and settings\n/result - (for admins) Get result table file\n/stop - (for admins) Stop taking events\n/setwelcome - (for admins) Set welcome message"))


@bot.message_handler(commands=["setwelcome"])
@restricted
def cmd_setwelcome(message):
    data["welcome"] = message.text[str(message.text + " ").find(" "):]
    save_data()
    bot.send_message(message.chat.id, ("Обновил приветствие"))

@bot.message_handler(commands=["chatid"])
@restricted
def cmd_chatid(message):
    bot.send_message(message.chat.id, ("Айди этого чата: %s"%(message.chat.id)))


@bot.message_handler(commands=["set"])
@restricted
def cmd_set(message):
    chunks = message.text.replace("@", "").split(" ")
    agentname = chunks[1]
    step = chunks[2]
    counter = chunks[3]
    value = int(chunks[4])
    if not step in ["start","end"]:
        bot.send_message(message.chat.id, ("вторым параметром должен быть start или end"))
        return
    if not counter in MODES and counter != 'AP':
        bot.send_message(message.chat.id, ("третьим параметром должен быть AP или "+ ",".join(MODES)))
        return
    if agentname not in data["counters"].keys():
        data["counters"][agentname] = {"start": {}, "end": {}}
    data["counters"][agentname][step][counter] = value
    save_data()
    if agentname in data["counters"].keys():
        txt = "Досье на: @%s\n"%(agentname)
        txt += user_info(agentname)
    else:
        txt = "Такой пользователь не найден в базе"
    bot.send_message(message.chat.id, (txt))


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
    bot.reply_to(message, ("Всё, я всё забыл :)"))


@bot.message_handler(commands=["startevent"])
@restricted
def cmd_startevent(message):
    data["getStart"] = True
    data["getEnd"] = False
    save_data()
    bot.send_message(message.chat.id, ("Принимаю скрины!"))


@bot.message_handler(commands=["endevent"])
@restricted
def cmd_endevent(message):
    data["getStart"] = False
    data["getEnd"] = True
    save_data()
    bot.send_message(message.chat.id, ("Принимаю скрины!"))


@bot.message_handler(commands=["stop"])
@restricted
def cmd_stop(message):
    data["getStart"] = False
    data["getEnd"] = False
    save_data()
    bot.send_message(message.chat.id, ("Не принимаю скрины!"))


@bot.message_handler(commands=["result"])
@restricted
def cmd_result(message):
    delimiter = message.text[len("/result "):len("/result ")+1]
    if delimiter == '':
        delimiter = ','
    txt = "Agent;Start_lvl;End_lvl;Start_AP;End_AP"
    for mode in MODES:
        txt += ";Start_%s;End_%s"%(mode,mode)
    txt += "\n"
    for agentname in data["counters"].keys():
        agentdata = {"start": {"AP": "-"}, "end": {"AP": "-"}}
        for mode in MODES:
            agentdata["start"][mode] = "-"
            agentdata["end"][mode] = "-"
        if "start" in data["counters"][agentname].keys():
            agentdata["start"].update(data["counters"][agentname]["start"])
        if "end" in data["counters"][agentname].keys():
            agentdata["end"].update(data["counters"][agentname]["end"])
        txt += '"%s";%s;%s;%s;%s'%(agentname, get_level(agentdata["start"]["AP"]), get_level(agentdata["end"]["AP"]), agentdata["start"]["AP"], agentdata["end"]["AP"])
        for mode in MODES:
            txt += ";%s;%s"%(agentdata["start"][mode], agentdata["end"][mode])
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
    txt = user_info(message.from_user.username);
    bot.send_message(message.chat.id, (txt))

@bot.message_handler(commands=["clearme"])
def cmd_clearme(message):
    if message.from_user.username in data["counters"].keys():
        del data["counters"][message.from_user.username]
        save_data()
        bot.reply_to(message, ("Ваши данные удалены"))
    else:
        bot.reply_to(message, ("Бот не располагает данными на вас"))

def user_info(username):
    MODES_PLUS_AP = ["AP"] + MODES
    if not username in data["counters"].keys():
        return 'Бот ничего не знает по вам'
    userData = data["counters"][username]
    print('userData', userData)
    txt = "== Стартовые показатели:"
    for mode in MODES_PLUS_AP:
        value = userData["start"].get(mode,"-")
        if mode == 'AP':
            txt += '\nLevel: %s'%(get_level(value))
        txt += "\n%s: %s"%(mode, value)
    if "end" in userData.keys() and len(userData['end'].keys()) > 0:
        txt += "\n== Финишные показатели:"
        for mode in MODES_PLUS_AP:
            start_value = userData["start"].get(mode,"-")
            value = userData["end"].get(mode,"-")
            if mode == 'AP':
                startLevel = get_level(start_value)
                endLevel = get_level(value)
                txt += '\nLevel: %s'%(get_level(value))
                if startLevel != endLevel:
                    txt += ' (+%s)'%(endLevel-startLevel)
            txt += "\n%s: %s"%(mode, value)
            if mode in userData["start"].keys() and mode in userData["end"].keys():
                delta = (userData["end"][mode] - userData["start"][mode]);
                txt += " (+%s)"%(delta)
    return txt


def get_level(AP):
   if AP == "-":
       AP = 0
   if AP >= 40000000:
       return 16
   elif AP >= 24000000:
       return 15
   elif AP >= 17000000:
       return 14
   elif AP >= 12000000:
       return 13
   elif AP >= 8400000:
       return 12
   elif AP >= 6000000:
       return 11
   elif AP >= 4000000:
       return 10
   elif AP >= 2400000:
       return 9
   elif AP >= 1200000:
       return 8
   elif AP >= 600000:
       return 7
   elif AP >= 300000:
       return 6
   elif AP >= 150000:
       return 5
   elif AP >= 70000:
       return 4
   elif AP >= 20000:
       return 3
   elif AP >= 2500:
       return 2
   else:
       return 1


@bot.message_handler(func=lambda message: True, content_types=["text"])
def process_msg(message):
    if message.chat.username in ADMINS:
        if message.text in data["counters"].keys():
            txt = "Досье на: @%s\n"%(message.text)
            txt += user_info(message.text)
        else:
            txt = "Такой пользователь не найден в базе"
        bot.send_message(message.chat.id, (txt))
    else:
        bot.reply_to(message, (data["welcome"]))


@bot.message_handler(func=lambda message: True, content_types=["photo"])
def process_photo(message):
    agentname = message.chat.username
    if (agentname == None):
        agentname = '%s' % message.chat.id
    if message.forward_from:
        if (message.chat.username in ADMINS) or (message.chat.username == message.forward_from.username):
            agentname = message.forward_from.username
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
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
    parseResult = parse_image(filename)
    if not data["getStart"] and not data["getEnd"]:
        txt = "Регистрация на эвент ещё не началась. На твоём изображении я вижу вот что:\n";
        if parseResult["success"]:
            txt += "Агент {}, AP {:,}, {} {:,}".format(agentname, parseResult["AP"], parseResult["mode"], parseResult[parseResult["mode"]])
        else:
            txt += "Данные с изображения распарсить не удалось"
        bot.send_message(message.chat.id, (txt))
        return
    if parseResult["success"]:
        if agentname not in data["counters"].keys():
            data["counters"][agentname] = {"pre":{}, "start": {}, "end": {}}
        data["counters"][agentname][datakey].update(parseResult)
        save_data()
        bot.reply_to(message, ("Изображение распознано. Проверьте правильность цифр:\n%s"%(user_info(agentname))))
        if data["okChat"]:
            bot.forward_message(data["okChat"], message.chat.id, message.message_id)
            bot.send_message(data["okChat"], "Агент {}, AP {:,}, {} {:,}".format(agentname, parseResult["AP"], parseResult["mode"], parseResult[parseResult["mode"]]))
    else:
        bot.reply_to(message, ("Не могу разобрать скрин! Отправьте другой, или зарегистрируйтесь у оргов вручную"))
        if data["failChat"] != 0:
            bot.forward_message(data["failChat"], message.chat.id, message.message_id)


if __name__ == "__main__":
    bot.polling(none_stop=True)
