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
            LOG.error('Exception: ' + str(e), exc_info=e)
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
    if "night" in data.keys() and data["night"]:
        # don't send notifications during night
        return
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


@bot.message_handler(commands=["night"])
@restricted
@log_incoming
def cmd_night(message):
    if "night" not in data.keys():
        data["night"] = False
    if not data["night"] and (data["getStart"] or data["getEnd"]):
        bot.reply_to(message, "Нельзя включить ночной режим во время эвента")
        return
    data["night"] = not data["night"]
    save_data()
    if data["night"]:
        bot.reply_to(message, "Ночной режим включен")
    else:
        bot.reply_to(message, "Ночной режим выключен")


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
        img = fraction_icon(fraction)
        txt += "@%s %s `%s`" % (agentname.replace('_', '\\_'), img, nick.replace('_', '\\_'))
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

    user_data = []
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
        is_anything_filled = False
        for mode in allowed_modes:
            if agentdata["start"][mode] != '-':
                is_anything_filled = True
            if agentdata["end"][mode] != '-':
                is_anything_filled = True
        if is_anything_filled:
            user_data.append((agentname, fraction, nick, agentdata["start"]["Level"], agentdata["start"]["AP"],
                              agentdata["start"]["Trekker"], agentdata["end"]["Level"], agentdata["end"]["AP"],
                              agentdata["end"]["Trekker"]))
    user_data.sort(key=itemgetter(1))
    for row in user_data:
        txt += '"%s";"%s";"%s";%s;%s;%s;%s;%s;%s\n' % row
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


@bot.message_handler(commands=["bestn"])
@log_incoming
def cmd_bestn(message):
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
                agent_nick = data["counters"][agentname].get('Nick', agentname)
                user_data.append({"agent_nick": agent_nick, "delta": delta, "fraction": fraction})
    user_data.sort(key=itemgetter('delta'), reverse=True)
    txt = 'Best %s:' % mode
    for i in range(amount):
        if i < len(user_data):
            user = user_data[i]
            img = fraction_icon(user['fraction'])
            txt += "\n#%s %s*%s* - %s" % (i + 1, img, user['agent_nick'], user['delta'])
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
    if len(message.text) > 100:
        return process_prime_tab_separated_text(message)
    if tg_name in ADMINS:
        user_tg_name = message.text.replace('@', '')
        if user_tg_name in data["counters"].keys():
            txt = user_info(user_tg_name)
        else:
            txt = "Такой пользователь не найден в базе"
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")
    else:
        bot.reply_to(message, WELCOME, parse_mode="Markdown")


def process_prime_tab_separated_text(message):
    msgid = message.message_id
    chatid = message.chat.id

    chunks = message.text.split("\n")
    if len(chunks) != 2:
        bot.send_message(chatid, "Не могу разобрать выгрузку! Возможно к тексту попала приписка Forwarded?")
        return
    title = chunks[0]
    titles = parse_title(title)
    values = chunks[1]

    regexp = re.compile('(.*)\s(\S+)\s(Enlightened|Resistance)\s(\d\d\d\d-\d\d-\d\d)\s(\d\d:\d\d:\d\d)\s([\s\d]+)')
    found = re.fullmatch(regexp, values)

    if not found:
        bot.forward_message(CHAT_FAIL, chatid, msgid)
        bot.send_message(chatid, "Не могу разобрать выгрузку! Отправьте пожалуйста скрин картинкой")
        return

    time_span = found[1]
    nick = found[2]
    fraction = 'e' if found[3] == 'Enlightened' else 'r'
    date = found[4]
    time = found[5]
    rest = found[6].split(' ')
    rest2 = [time_span, nick, fraction, date, time] + rest

    if time_span in ['ЗА МЕСЯЦ', 'MONTH']:
        bot.send_message(chatid, 'Вы прислали месячную стату. А нужно "за всё время"')
        return

    if time_span in ['ЗА НЕДЕЛЮ', 'WEEK']:
        bot.send_message(chatid, 'Вы прислали недельную стату. А нужно "за всё время"')
        return

    if time_span in ['СЕЙЧАС', 'NOW'] or 'ActivePortalsOwned' in titles:
        bot.send_message(chatid, 'Вы прислали дневную стату. А нужно "за всё время"')
        return

    if len(titles) != len(rest2):
        LOG.info(titles)
        LOG.info(rest2)
        bot.forward_message(CHAT_FAIL, chatid, msgid)
        bot.send_message(chatid, "Не могу разобрать выгрузку - обнаружен неизвестный боту параметр. Отправьте пожалуйста скрин картинкой")
        return

    decoded = {}
    for i in range(len(rest2)):
        val = rest2[i]
        if re.fullmatch(r'\d+', val):
            val = int(val)
        decoded[titles[i]] = val

    LOG.info('decoded ' + str(decoded))
    decoded['Level'] = calc_level(decoded)

    agentname = get_tg_nick(message)
    if message.forward_from:
        if (agentname in ADMINS) or (agentname == message.forward_from.username):
            agentname = message.forward_from.username
    else:
        user_save_chatid(agentname, message.chat.id)

    if data["getStart"]:
        datakey = "start"
    elif data["getEnd"]:
        datakey = "end"
    else:
        datakey = "pre"

    if not data["getStart"] and not data["getEnd"]:
        txt = "Регистрация на эвент ещё не началась. На твоей выгрузке я вижу вот что:\n"
        d = decoded
        fraction = full_fraction_name(d['Fraction'])
        txt += "Fraction *%s*\nAP *%s*\nLvl *%s*\n" % (
            fraction, d["AP"], d["Level"])
        for mode in MODES:
            if mode in d.keys():
                txt += "%s *%s*\n" % (mode, d[mode])
        bot.send_message(chatid, txt, parse_mode="Markdown")
        return
    data["counters"][agentname]['Nick'] = decoded['Nick']
    data["counters"][agentname]['fraction'] = decoded['Fraction']
    data["counters"][agentname][datakey].update(decoded)
    save_data()
    user_inform(agentname)
    bot.forward_message(CHAT_OK, chatid, msgid)
    bot.send_message(CHAT_OK, "Parsed: " + str(decoded))


def parse_title(title):
    title = str(title).replace('Time Span', 'TimeSpan')
    title = str(title).replace('Agent Name', 'Nick')
    title = str(title).replace('Agent Faction', 'Fraction')
    title = str(title).replace('Date (yyyy-mm-dd)', 'Date')
    title = str(title).replace('Time (hh:mm:ss)', 'Time')
    title = str(title).replace('Lifetime AP', 'AP')
    title = str(title).replace('Current AP', 'CurrentAP')
    title = str(title).replace('Unique Portals Visited', 'Explorer')
    title = str(title).replace('Portals Discovered', 'PortalsDiscovered')
    title = str(title).replace('Seer Points', 'Seer')
    title = str(title).replace('XM Collected', 'XMCollected')
    title = str(title).replace('OPR Agreements', 'OprAgreements')
    title = str(title).replace('Distance Walked', 'Trekker')
    title = str(title).replace('Resonators Deployed', 'Builder')
    title = str(title).replace('Links Created', 'Connector')
    title = str(title).replace('Control Fields Created', 'MindController')
    title = str(title).replace('Mind Units Captured', 'Illuminator')
    title = str(title).replace('Longest Link Ever Created', 'LongestLinkEverCreated')
    title = str(title).replace('Largest Control Field', 'LargestControlField')
    title = str(title).replace('XM Recharged', 'Recharger')
    title = str(title).replace('Unique Portals Captured', 'Pioneer')
    title = str(title).replace('Portals Captured', 'Liberator')
    title = str(title).replace('Mods Deployed', 'Engineer')
    title = str(title).replace('Resonators Destroyed', 'Purifier')
    title = str(title).replace('Portals Neutralized', 'PortalsNeutralized')
    title = str(title).replace('Enemy Links Destroyed', 'EnemyLinksDestroyed')
    title = str(title).replace('Enemy Fields Destroyed', 'EnemyFieldsDestroyed')
    title = str(title).replace('Max Time Portal Held', 'Guardian')
    title = str(title).replace('Max Time Link Maintained', 'MaxTimeLinkMaintained')
    title = str(title).replace('Max Link Length x Days', 'MaxLinkLengthxDays')
    title = str(title).replace('Max Time Field Held', 'MaxTimeFieldHeld')
    title = str(title).replace('Largest Field MUs x Days', 'LargestFieldMUsxDays')
    title = str(title).replace('Unique Missions Completed', 'SpecOps')
    title = str(title).replace('Hacks', 'Hacker')
    title = str(title).replace('Glyph Hack Points', 'Translator')
    title = str(title).replace('Longest Hacking Streak', 'Sojourner')
    title = str(title).replace('Agents Successfully Recruited', 'AgentsSuccessfullyRecruited')
    title = str(title).replace('Mission Day(s) Attended', 'MissionDay')
    title = str(title).replace('NL-1331 Meetup(s) Attended', 'NL1331Meetup')
    title = str(title).replace('First Saturday Events', 'FirstSaturday')
    title = str(title).replace('Recursions', 'Recursions')
    title = str(title).replace('Active Portals Owned', 'ActivePortalsOwned')
    title = str(title).replace('Control Fields Active', 'ActivePortalsOwned')
    title = str(title).replace('Mind Unit Control', 'MindUnitControl')
    title = str(title).replace('Current Hacking Streak', 'CurrentHackingStreak')
    title = str(title).replace('Clear Fields Events', 'ClearField')
    title = str(title).replace('Prime Challenges', 'PrimeChallenges')
    title = str(title).replace('Stealth Ops Missions', 'StealthOps')
    ans = title.split(' ')
    ans.pop()
    return ans


def calc_level(parsed):
    # LOG.info('calc_level ' + str(parsed))
    k = 1000
    m = 1000 * 1000
    levels_ap_required = [2500, 20*k, 70*k, 150*k, 0.3*m, 0.6*m, 1.2*m, 2.4*m, 4*m, 6*m, 8.4*m, 12*m, 17*m, 24*m, 40*m]

    if not parsed['CurrentAP']:
        return None

    level = 1
    for level_ap_needed in levels_ap_required:
        if parsed['CurrentAP'] >= level_ap_needed:
            level += 1

    if 'Recursions' in parsed.keys() and parsed['Recursions'] > 0:
        # skip medals checking for recursed agents
        return level
    if level <= 8:
        # no medals requirements for 8- levels
        return level

    medals = {}
    medals['Sojourner'] = [30, 60, 180, 360]
    medals['Illuminator'] = [50*k, 250*k, 1*m, 4*m]
    medals['Translator'] = [2*k, 6*k, 20*k, 50*k]
    medals['Recruiter'] = [10, 25, 50, 100]
    medals['Trekker'] = [100, 300, 1000, 2500]
    medals['Engineer'] = [1500, 5*k, 20*k, 50*k]
    medals['SpecOps'] = [25, 100, 200, 500]
    medals['Recharger'] = [1*m, 3*m, 10*m, 25*m]
    medals['Connector'] = [1*k, 5*k, 25*k, 100*k]
    medals['Builder'] = [10*k, 30*k, 100*k, 200*k]
    medals['Explorer'] = [1*k, 2*k, 10*k, 30*k]
    medals['Guardian'] = [10, 20, 90, 150]
    medals['Hacker'] = [10*k, 30*k, 100*k, 200*k]
    medals['MindController'] = [500, 2*k, 10*k, 40*k]
    medals['Purifier'] = [10*k, 30*k, 100*k, 300*k]
    medals['Liberator'] = [1*k, 5*k, 15*k, 40*k]
    medals['Pioneer'] = [200, 1*k, 5*k, 20*k]
    medals['Recon'] = [750, 2500, 5*k, 10*k]
    medals['MissionDay'] = [3, 6, 10, 20]
    medals['NL1331Meetup'] = [5, 10, 25, 50]
    medals['MissionDay'] = [3, 6, 10, 20]
    medals['FirstSaturday'] = [6, 12, 24, 36]

    player_has_medals = [0, 0, 0, 0]

    for medal_name in medals:
        if medal_name in parsed.keys():
            medal_requirements = medals[medal_name]
            i = -1
            for treshold in medal_requirements:
                if parsed[medal_name] >= treshold:
                    i += 1
            # if i == 1:
            #    LOG.info('silver: ' + medal_name)
            if i > -1:
                player_has_medals[i] += 1

    LOG.info('player_has_medals ' + str(player_has_medals))

    player_has_medals[0] += player_has_medals[1] + player_has_medals[2] + player_has_medals[3]
    player_has_medals[1] += player_has_medals[2] + player_has_medals[3]
    player_has_medals[2] += player_has_medals[3]

    LOG.info('player_has_medals normalized ' + str(player_has_medals))

    medals_required_for_each_level = {}
    medals_required_for_each_level[8] = [0, 0, 0, 0]
    medals_required_for_each_level[9] = [4, 1, 0, 0]
    medals_required_for_each_level[10] = [5, 2, 0, 0]
    medals_required_for_each_level[11] = [6, 4, 0, 0]
    medals_required_for_each_level[12] = [7, 6, 0, 0]
    medals_required_for_each_level[13] = [0, 7, 1, 0]
    medals_required_for_each_level[14] = [0, 0, 2, 0]
    medals_required_for_each_level[15] = [0, 0, 3, 0]
    medals_required_for_each_level[16] = [0, 0, 4, 2]

    while not pass_level_requirements(player_has_medals, medals_required_for_each_level[level]):
        level -= 1

    return level


def pass_level_requirements(player_medals, medals_required):
    for i in range(4):
        if player_medals[i] < medals_required[i]:
            return False
    return True


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
        if decoded.get('mode') in MODES:
            if decoded['fraction']:
                data["counters"][agentname]['fraction'] = decoded['fraction']
            data["counters"][agentname][datakey].update(decoded)
            save_data()
            user_inform(agentname)
            bot.forward_message(CHAT_OK, chatid, msgid)
            bot.send_message(CHAT_OK, "Агент %s, AP %s, %s %s" % (
                agentname, decoded["AP"], decoded["mode"], decoded[decoded["mode"]]))
        else:
            bot.send_message(chatid, "Вы прислали скрин из неактивной категории *%s*. Пришлите вместо него *%s*" %
                             (decoded.get('mode'), ', '.join(MODES)), parse_mode="Markdown")
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
