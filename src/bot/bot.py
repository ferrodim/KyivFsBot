#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
import telebot
import json
import random
import string
import re
import pika
import logging
import threading
from operator import itemgetter
from config import ADMINS, MODES, API_TOKEN, WELCOME, CHAT_OK, CHAT_FAIL
from queue import Queue

print("restart")

bot = telebot.TeleBot(API_TOKEN, threaded=False)
try:
    datafile = open("base.txt", "r")
    data = json.load(datafile)
except FileNotFoundError:
    data = {}
    datafile = open("base.txt", "w")
    json.dump(data, datafile, ensure_ascii=False)
if "getStart" not in data.keys():
    data["getStart"] = False
if "getEnd" not in data.keys():
    data["getEnd"] = False
if "counters" not in data.keys():
    data["counters"] = {}
if "notify" not in data.keys():
    data["notify"] = False
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
            bot.reply_to(message, "Доступ запрещён")
            return
        return func(message, *args, **kwargs)

    return wrapped


def log_incoming(func):
    @wraps(func)
    def wrapped(message, *args, **kwargs):
        try:
            LOG.info(get_tg_nick(message) + ' <- ' + message.text)
            return func(message, *args, **kwargs)
        except Exception as e:
            LOG.error('Exception: ' + str(e))
    return wrapped


@bot.message_handler(commands=["start"])
@log_incoming
def cmd_start(message):
    bot.reply_to(message, WELCOME, parse_mode="Markdown")


@bot.message_handler(commands=["help"])
@log_incoming
def cmd_help(message):
    txt = "/me - View personal userinfo\n" \
          "/nick %your_in_game_nick% - Set your in_game nick\n" \
          "/fraction %e_or_r% - Set your fraction\n" \
          "/clearme - Delete you account\n"
    if get_tg_nick(message) in ADMINS:
        txt += "== admin commands\n" \
               "@username or username - Get userinfo\n" \
               "/startevent - Begin taking start screenshots\n" \
               "/endevent - Begin taking final screenshots\n" \
               "/stop - Stop taking events\n" \
               "/notify - Toggle notification of agents\n" \
               "/sendall - Send message to all agents\n" \
               "/agents - Get agents table\n" \
               "/result - Get result table file\n" \
               "/resultfev - Get result table file in FEV style\n" \
               "/best <category> Get best results\n" \
               "/clear <tg_nick> Clear by tg_nick\n" \
               "/clearzero Clear agents by zero results\n" \
               "/softreset - Clear everything exept nick and fraciton\n" \
               "/reset - Clear all data and settings\n" \
               "/set tg_nick start Param Value - Set start value (AP, Level...)\n" \
               "/set tg_nick end Param Value - Set start value (AP, Level...)\n" \
               "/set tg_nick Nick ingame_nick - Set ingame nick for selected user"
    bot.reply_to(message, txt, parse_mode="Markdown")


@bot.message_handler(commands=["chatid"])
@restricted
@log_incoming
def cmd_chatid(message):
    bot.send_message(message.chat.id, "Айди этого чата: %s" % message.chat.id)


@bot.message_handler(commands=["set"])
@restricted
@log_incoming
def cmd_set(message):
    allowed_modes = ["AP", "Level"] + MODES
    modes_lowercased = {}
    for x in allowed_modes:
        modes_lowercased[x.lower()] = x
    chunks = message.text.replace("@", "").replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) == 4 and chunks[2] in ['Nick', 'fraction']) or \
                     (len(chunks) == 5 and chunks[2] in ["start", "end"] and
                      (chunks[3] in allowed_modes or chunks[3] in modes_lowercased.keys()))
    if len(chunks) == 4 and chunks[2] == 'fraction' and not chunks[3] in ['e', 'r', '']:
        is_valid_query = False
    if not is_valid_query:
        bot.send_message(message.chat.id, ("Неверный формат запроса. Нужно писать:\n"
                                           "`/set telegram_nick start Param value`\n"
                                           "`/set telegram_nick end Param value`\n"
                                           "`/set telegram_nick fraction e/r`\n"
                                           "`/set telegram_nick Nick game_nick`"), parse_mode="Markdown")
        return
    agentname = chunks[1]
    if agentname not in data["counters"].keys():
        data["counters"][agentname] = {"start": {}, "end": {}}
    if chunks[2] == 'Nick':
        value = chunks[3]
        data["counters"][agentname]['Nick'] = value
    elif chunks[2] == 'fraction':
        value = chunks[3]
        data["counters"][agentname]['fraction'] = value
    else:
        step = chunks[2]
        counter = chunks[3]
        if counter in modes_lowercased.keys():
            counter = modes_lowercased[counter]
        value = int(chunks[4])
        data["counters"][agentname][step][counter] = value
    save_data()
    bot.reply_to(message, "Done\n" + user_info(agentname), parse_mode="Markdown")
    if message.from_user.username != agentname:
        user_inform(agentname)


def user_inform(agentname):
    if agentname in data["counters"]:
        chatid = data["counters"][agentname].get('chatid')
        if chatid is not None:
            txt = 'Данные по вам изменились:\n' + user_info(agentname)
            bot.send_message(chatid, txt, parse_mode="Markdown")


@bot.message_handler(commands=["sendall"])
@restricted
def cmd_send_all(message):
    agents_total = 0
    agents_received = 0
    text = message.text[len('/sendall '):]
    for agentname in data["counters"].keys():
        agents_total += 1
        chat_id = data["counters"][agentname].get('chatid', '')
        if chat_id:
            agents_received += 1
            bot.send_message(chat_id, "Агент, вам сообщение от организаторов:\n\n" + text)
    bot.reply_to(message, "Массовое сообщение доставленно %s/%s агентам" % (agents_received, agents_total))


@bot.message_handler(commands=["softreset"])
@restricted
@log_incoming
def cmd_softreset(message):
    if message.text != '/softreset ok':
        bot.reply_to(message, "Вы правда хотите очистить всю базу, кроме ников?\n\n"
                              "Введите */softreset ok*, если да", parse_mode="Markdown")
        return
    data["getStart"] = False
    data["getEnd"] = False
    for agentname in data["counters"].keys():
        data["counters"][agentname]['start'] = {}
        data["counters"][agentname]['end'] = {}
    save_data()
    bot.reply_to(message, "База данных очищена")


@bot.message_handler(commands=["reset"])
@restricted
@log_incoming
def cmd_reset(message):
    if message.text != '/reset ok':
        bot.reply_to(message, "Вы правда хотите очистить всю базу?\n\n"
                              "Введите */reset ok*, если да", parse_mode="Markdown")
        return
    data.clear()
    data["getStart"] = False
    data["getEnd"] = False
    data["counters"] = {}
    data["notify"] = False
    save_data()
    bot.reply_to(message, "База данных очищена")


@bot.message_handler(commands=["notify"])
@restricted
@log_incoming
def cmd_notify(message):
    data["notify"] = not data["notify"]
    save_data()
    if data["notify"]:
        bot.reply_to(message, "Уведомление агентов включено")
    else:
        bot.reply_to(message, "Уведомление агентов выключено")


@bot.message_handler(commands=["agents"])
@restricted
@log_incoming
def cmd_agents(message):
    txt = "Зарегистрированные агенты"
    agents_total = 0
    agents_enl = 0
    agents_res = 0
    agents_nick = 0
    agents_fraction = 0
    for agentname in data["counters"].keys():
        agents_total += 1
        fraction = data["counters"][agentname].get("fraction", "-")
        nick = data["counters"][agentname].get("Nick", "-")
        if fraction == "e":
            agents_enl += 1
        if fraction == "r":
            agents_res += 1
        if nick == "-":
            agents_nick += 1
        if fraction == "-":
            agents_fraction += 1
    txt += "\nВсего: %d Enl: %d Res: %d" % (agents_total, agents_enl, agents_res)
    if agents_nick or agents_fraction:
        txt += "\nБез ника: %d Без фракции: %d" % (agents_nick, agents_fraction)
    for agentname in data["counters"].keys():
        txt += "\n"
        nick = data["counters"][agentname].get("Nick", "-")
        fraction = data["counters"][agentname].get("fraction", "-")  # \U0001F438 Frog  \U0001F41F Fish
        txt += "@%s / `%s` / %s" % (agentname.replace('_', '\\_'), nick.replace('_', '\\_'), fraction)
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")


@bot.message_handler(commands=["startevent"])
@restricted
@log_incoming
def cmd_startevent(message):
    data["getStart"] = True
    data["getEnd"] = False
    save_data()
    if data["notify"]:
        for agentname in data["counters"].keys():
            bot.send_message(data["counters"][agentname]['chatid'], "Принимаю стартовые скрины!")
    else:
        bot.send_message(message.chat.id, "Принимаю стартовые скрины!")


@bot.message_handler(commands=["endevent"])
@restricted
@log_incoming
def cmd_endevent(message):
    data["getStart"] = False
    data["getEnd"] = True
    save_data()
    if data["notify"]:
        for agentname in data["counters"].keys():
            bot.send_message(data["counters"][agentname]['chatid'], "Принимаю финишные скрины!")
    else:
        bot.send_message(message.chat.id, "Принимаю финишные скрины!")


@bot.message_handler(commands=["stop"])
@restricted
@log_incoming
def cmd_stop(message):
    data["getStart"] = False
    data["getEnd"] = False
    save_data()
    if data["notify"]:
        for agentname in data["counters"].keys():
            bot.send_message(data["counters"][agentname]['chatid'], "Прием скринов закончен.")
    else:
        bot.send_message(message.chat.id, "Прием скринов закончен.")


@bot.message_handler(commands=["result"])
@restricted
@log_incoming
def cmd_result(message):
    delimiter = message.text[len("/result "):len("/result ") + 1]
    if delimiter == '':
        delimiter = ','
    txt = "TG_nick;Game_nick;Fraction"
    allowed_modes = ["AP", "Level"] + MODES
    for mode in allowed_modes:
        txt += ";Start_%s;End_%s;Delta_%s" % (mode, mode, mode)
    txt += "\n"
    for agentname in data["counters"].keys():
        agentdata = {"start": {}, "end": {}}
        for mode in allowed_modes:
            agentdata["start"][mode] = "-"
            agentdata["end"][mode] = "-"
        if "start" in data["counters"][agentname].keys():
            agentdata["start"].update(data["counters"][agentname]["start"])
        if "end" in data["counters"][agentname].keys():
            agentdata["end"].update(data["counters"][agentname]["end"])
        nick = data["counters"][agentname].get("Nick", "-")
        fraction = data["counters"][agentname].get("fraction", "-")
        txt += '"%s";"%s";"%s"' % (agentname, nick, fraction)
        for mode in allowed_modes:
            if isinstance(agentdata["end"][mode], int) and isinstance(agentdata["start"][mode], int):
                delta = agentdata["end"][mode] - agentdata["start"][mode]
            else:
                delta = '-'
            txt += ";%s;%s;%s" % (agentdata["start"][mode], agentdata["end"][mode], delta)
        txt += "\n"
    txt = txt.replace(';', delimiter)
    resultfile = open("result.csv", "w")
    resultfile.write(txt)
    resultfile.close()
    resultfile = open("result.csv", "rb")
    bot.send_document(message.chat.id, resultfile)
    resultfile.close()


@bot.message_handler(commands=["resultfev"])
@restricted
@log_incoming
def cmd_resultfev(message):
    delimiter = message.text[len("/resultfev "):len("/resultfev ") + 1]
    if delimiter == '':
        delimiter = ','
    txt = "TG_nick;Fraction;Game_nick;Start_Level;Start_AP,Start_Trekker;End_Level;End_AP;End_Trekker"
    allowed_modes = ["Level", "AP", "Trekker"]
    txt += "\n"
    for agentname in data["counters"].keys():
        agentdata = {"start": {}, "end": {}}
        for mode in allowed_modes:
            agentdata["start"][mode] = "-"
            agentdata["end"][mode] = "-"
        if "start" in data["counters"][agentname].keys():
            agentdata["start"].update(data["counters"][agentname]["start"])
        if "end" in data["counters"][agentname].keys():
            agentdata["end"].update(data["counters"][agentname]["end"])
        nick = data["counters"][agentname].get("Nick", "-")
        fraction = data["counters"][agentname].get("fraction", "-")
        txt += '"%s";"%s";"%s"' % (agentname, fraction, nick)
        txt += ";%s;%s;%s" % (agentdata["start"]["Level"], agentdata["start"]["AP"], agentdata["start"]["Trekker"])
        txt += ";%s;%s;%s" % (agentdata["end"]["Level"], agentdata["end"]["AP"], agentdata["end"]["Trekker"])
        txt += "\n"
    txt = txt.replace(';', delimiter)
    resultfile = open("resultfev.csv", "w")
    resultfile.write(txt)
    resultfile.close()
    resultfile = open("resultfev.csv", "rb")
    bot.send_document(message.chat.id, resultfile)
    resultfile.close()


def category_name_normalize(name):
    allowed_modes = ["AP", "Level"] + MODES
    for mode in allowed_modes:
        if name.lower() == mode.lower():
            return mode
    if name in ['lvl']:
        return 'Level'
    return ''


def fraction_icon(fraction):
    if fraction == "e":
        # return "\U0001F438"
        return "\U0001F49A"
    elif fraction == "r":
        # return "\U0001F41F"
        return "\U0001F499"
    else:
        return ""


@bot.message_handler(commands=["best"])
@restricted
@log_incoming
def cmd_best(message):
    allowed_modes = ["AP", "Level"] + MODES
    chunks = message.text.replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) in [2, 3] and (category_name_normalize(chunks[1]) in allowed_modes))
    amount = int(chunks[2]) if len(chunks) == 3 else 10
    if not is_valid_query:
        bot.send_message(message.chat.id, ("Неверный формат запроса. Нужно писать:\n"
                                           "`/best <category>`\n"
                                           "где category принимает значения\n"
                                           "" + ', '.join(allowed_modes)), parse_mode="Markdown")
        return
    mode = category_name_normalize(chunks[1])
    bot.send_message(message.chat.id, "Вы запросили инфу по " + mode)
    user_data = []
    for agentname in data["counters"].keys():
        if "start" in data["counters"][agentname].keys() and "end" in data["counters"][agentname].keys():
            if mode in data["counters"][agentname]['start'] and mode in data["counters"][agentname]['end']:
                delta = data["counters"][agentname]['end'][mode] - data["counters"][agentname]['start'][mode]
                fraction = data["counters"][agentname].get('fraction', '-')
                user_data.append({"agentname": agentname, "delta": delta, "fraction": fraction})
    user_data.sort(key=itemgetter('delta'), reverse=True)
    txt = 'Best %s:' % mode
    for i in range(amount):
        if i < len(user_data):
            user = user_data[i]
            img = fraction_icon(user['fraction'])
            txt += "\n#%s %s*%s* - %s" % (i + 1, img, user['agentname'], user['delta'])
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")


@bot.message_handler(commands=["clearzero"])
@restricted
@log_incoming
def cmd_clearzero(message):
    if message.text != '/clearzero ok':
        bot.reply_to(message, "Вы правда хотите удалить данные c нулевой стартовой статистикой?\n\n"
                              "Введите */clearzero ok*, если да", parse_mode="Markdown")
        return
    agents_to_delete = {}
    for agentname in data["counters"].keys():
        ap = data["counters"][agentname]["start"].get("AP", "")
        trekker = data["counters"][agentname]["start"].get("Trekker", "")
        if (not ap) and (not trekker):
            agents_to_delete[agentname] = True
    for agentname in agents_to_delete:
        del data["counters"][agentname]
    save_data()
    bot.reply_to(message, "Удалено %d записей с нулевой стартовой статистикой" % len(agents_to_delete))


@bot.message_handler(commands=["clear"])
@restricted
@log_incoming
def cmd_clear(message):
    chunks = message.text.replace("@", "").replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) == 2 and re.fullmatch(r'[a-zA-Z0-9\-_]+', chunks[1]))
    if not is_valid_query:
        bot.send_message(message.chat.id, ("Неверный формат запроса. Нужно писать:\n"
                                           "`/clear telegram_nick`\n"), parse_mode="Markdown")
        return
    tg_name = chunks[1]
    if tg_name in data["counters"].keys():
        del data["counters"][tg_name]
        save_data()
        bot.reply_to(message, "Данные @%s удалены" % tg_name)
    else:
        bot.reply_to(message, "Бот не располагает данными на @%s" % tg_name)


@bot.message_handler(commands=["me"])
@log_incoming
def cmd_me(message):
    tg_name = get_tg_nick(message)
    txt = user_info(tg_name)
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")


@bot.message_handler(commands=["clearme"])
@log_incoming
def cmd_clearme(message):
    if message.text != '/clearme ok':
        bot.reply_to(message, "Вы правда хотите удалить свои данные?\n\n"
                              "Введите */clearme ok*, если да", parse_mode="Markdown")
        return
    tg_name = get_tg_nick(message)
    if tg_name in data["counters"].keys():
        del data["counters"][tg_name]
        save_data()
        bot.reply_to(message, "Ваши данные удалены")
    else:
        bot.reply_to(message, "Бот не располагает данными на вас")


@bot.message_handler(commands=["fraction"])
@log_incoming
def cmd_fraction(message):
    chunks = message.text.replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) == 2 and re.fullmatch(r'[er]', chunks[1]))
    if not is_valid_query:
        bot.send_message(message.chat.id, ("Неверный формат запроса. Нужно писать:\n"
                                           "`/fraction e`\n`/fraction r`"), parse_mode="Markdown")
        return
    tg_name = get_tg_nick(message)
    fraction = chunks[1]
    if tg_name not in data["counters"].keys():
        data["counters"][tg_name] = {"start": {}, "end": {}}
    data["counters"][tg_name]['fraction'] = fraction
    save_data()
    user_save_chatid(tg_name, message.chat.id)
    txt = user_info(tg_name)
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")


@bot.message_handler(commands=["nick"])
@log_incoming
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
    user_save_chatid(tg_name, message.chat.id)
    txt = user_info(tg_name)
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")


def user_info(username):
    allowed_modes = ["AP", "Level"] + MODES
    if username not in data["counters"].keys():
        return 'Бот ничего не знает по вам'
    user_data = data["counters"][username]
    txt = "Ник телеги: @%s\n" % username.replace('_', '\\_')
    game_nick = user_data.get("Nick", "-")
    if game_nick != '-':
        txt += "Ник в игре: %s\n" % game_nick.replace('_', '\\_')
    fraction = user_data.get("fraction", "")
    if fraction:
        txt += "Фракция: %s\n" % full_fraction_name(fraction)
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
    if tg_nick is None:
        tg_nick = '#' + str(message.chat.id)
    return tg_nick


@bot.message_handler(func=lambda message: True, content_types=["text"])
@log_incoming
def process_msg(message):
    if message.chat.id < 0:
        return
    tg_name = get_tg_nick(message)
    if tg_name in ADMINS:
        user_tg_name = message.text.replace('@', '')
        if user_tg_name in data["counters"].keys():
            txt = user_info(user_tg_name)
        else:
            txt = "Такой пользователь не найден в базе"
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")
    else:
        bot.reply_to(message, WELCOME, parse_mode="Markdown")


@bot.message_handler(func=lambda message: True, content_types=["photo"])
def process_photo(message):
    agentname = get_tg_nick(message)
    if message.forward_from:
        if (agentname in ADMINS) or (agentname == message.forward_from.username):
            agentname = message.forward_from.username
    bot.send_message(message.chat.id, "\U000023F3 Подождите", parse_mode="Markdown")
    user_save_chatid(agentname, message.chat.id)
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = agentname + "_"
    if data["getStart"]:
        datakey = "start"
    elif data["getEnd"]:
        datakey = "end"
    else:
        datakey = "pre"
    postfix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    filename += datakey + "_" + str(postfix) + ".jpg"
    LOG.info(agentname + ' <- IMG ' + filename)
    with open("/Screens/" + filename, "wb") as new_file:
        new_file.write(downloaded_file)
    decode_query = {}
    decode_query['img'] = filename
    decode_query['msgid'] = message.message_id
    decode_query['chatid'] = message.chat.id
    decode_query['datakey'] = datakey
    decode_query['agentname'] = agentname
    write_queue.put(json.dumps(decode_query))


def full_fraction_name(short_name):
    if short_name == 'e':
        return 'Enlight'
    elif short_name == 'r':
        return 'Resist'
    else:
        return 'Unknown'


def on_message(channel, method_frame, header_frame, body):
    LOG.info('{Rabbit} <= %s', body)
    decoded = json.loads(body)
    msgid = decoded['msgid']
    chatid = decoded['chatid']
    datakey = decoded['datakey']
    agentname = decoded['agentname']
    if not data["getStart"] and not data["getEnd"]:
        txt = "Регистрация на эвент ещё не началась. На твоём изображении я вижу вот что:\n"
        if decoded["success"]:
            # txt += "\n_%s_: *%s*" % (mode, value)
            d = decoded
            fraction = full_fraction_name(d['fraction'])
            txt += "Fraction *%s*\nAP *%s*\nLvl *%s*\n%s *%s*" % (
                fraction, d["AP"], d["Level"], d["mode"], d[d["mode"]])
        else:
            txt += "Данные с изображения распарсить не удалось"
        bot.send_message(chatid, txt, parse_mode="Markdown")
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        return
    if "success" in decoded.keys() and decoded["success"]:
        if decoded['fraction']:
            data["counters"][agentname]['fraction'] = decoded['fraction']
        data["counters"][agentname][datakey].update(decoded)
        save_data()
        user_inform(agentname)
        bot.forward_message(CHAT_OK, chatid, msgid)
        bot.send_message(CHAT_OK, "Агент %s, AP %s, %s %s" % (
            agentname, decoded["AP"], decoded["mode"], decoded[decoded["mode"]]))
    else:
        bot.forward_message(CHAT_FAIL, chatid, msgid)
        bot.send_message(chatid, "Не могу разобрать скрин! Отправьте другой, или зарегистрируйтесь у оргов вручную")
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def user_save_chatid(agentname, chatid):
    if chatid > 0:
        if agentname not in data["counters"].keys():
            data["counters"][agentname] = {"pre": {}, "start": {}, "end": {}}
            save_data()
        if data["counters"][agentname].get('chatid') != chatid:
            data["counters"][agentname]['chatid'] = chatid
            save_data()


def rabbit_read_thread():
    credentials2 = pika.PlainCredentials('rabbitmq', 'rabbitmq')
    parameters2 = pika.ConnectionParameters("rabbit", 5672, '/', credentials2, frame_max=20000)
    connection2 = pika.BlockingConnection(parameters2)
    channel_read = connection2.channel()
    channel_read.basic_qos(prefetch_count=1)
    channel_read.exchange_declare(exchange='main', exchange_type='direct', durable=True)
    channel_read.queue_declare(queue='bot', durable=True)
    channel_read.queue_declare(queue='decoders', durable=True)
    channel_read.queue_bind('bot', 'main', 'parseResult')
    channel_read.queue_bind('decoders', 'main', 'parseRequest')
    channel_read.basic_consume('bot', on_message)
    try:
        channel_read.start_consuming()
    except KeyboardInterrupt:
        channel_read.stop_consuming()


def rabbit_write_thread():
    credentials = pika.PlainCredentials('rabbitmq', 'rabbitmq')
    parameters = pika.ConnectionParameters("rabbit", 5672, '/', credentials, heartbeat=None)
    connection = pika.BlockingConnection(parameters)
    channel_write = connection.channel()
    channel_write.exchange_declare(exchange='main', exchange_type='direct', durable=True)
    channel_write.queue_declare(queue='bot', durable=True)
    channel_write.queue_declare(queue='decoders', durable=True)
    channel_write.queue_bind('bot', 'main', 'parseResult')
    channel_write.queue_bind('decoders', 'main', 'parseRequest')
    while True:
        if not write_queue.empty():
            msg = write_queue.get(timeout=1000)
            LOG.info('{Rabbit} => %s', msg)
            channel_write.basic_publish('main', 'parseRequest', msg)
            write_queue.task_done()
        connection.process_data_events()
        connection.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOG = logging.getLogger(__name__)
    write_queue = Queue()
    threading.Thread(target=rabbit_read_thread, args=()).start()
    threading.Thread(target=rabbit_write_thread, args=()).start()
    bot.infinity_polling(timeout=5, interval=1, none_stop=True)
