#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
import json
# import random
# import string
import re
import pika
import logging
from operator import itemgetter

print("restart")

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
        if not message['isAdmin']:
            # bot.reply_to(message, _("Доступ запрещён"))
            send_message(_("Доступ запрещён"), message['chat']['id'])
            return
        return func(message, *args, **kwargs)

    return wrapped


def cmd_help(message, city):
    txt = "/me - View personal userinfo\n" \
          "/lang - Change language to ua/ru/en\n" \
          "/start - See general info\n" \
          "/best <category> Get best results\n" \
          "/bestn <category> Get best results\n"\
          "/bestabsolute <category> Get best results\n" \
          "/clearme - Delete you account\n"
    if message['isAdmin']:
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
               "/clear <tg_nick> Clear by tg_nick\n" \
               "/clearzero Clear agents by zero results\n" \
               "/softreset - Clear everything exept nick and fraciton\n" \
               "/reset - Clear all data and settings\n" \
               "/set tg_nick start Param Value - Set start value (AP, Level...)\n" \
               "/set tg_nick end Param Value - Set start value (AP, Level...)\n" \
               "/set tg_nick Nick ingame_nick - Set ingame nick for selected user"
    reply_to(message, txt, parse_mode="Markdown")


@restricted
def cmd_set(message, city):
    allowed_modes = ["AP", "Level"] + city['modes']
    modes_lowercased = {}
    for x in allowed_modes:
        modes_lowercased[x.lower()] = x
    chunks = message['text'].replace("@", "").replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) == 4 and chunks[2] in ['Nick', 'fraction']) or \
                     (len(chunks) == 5 and chunks[2] in ["start", "end"] and
                      (chunks[3] in allowed_modes or chunks[3] in modes_lowercased.keys()))
    if len(chunks) == 4 and chunks[2] == 'fraction' and not chunks[3] in ['e', 'r', '']:
        is_valid_query = False
    if not is_valid_query:
        reply_to(message, ("Неверный формат запроса. Нужно писать:\n"
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
    reply_to(message, _("Done"), parse_mode="Markdown")
    reply_user_info(message['chat']['id'], agentname, city)
    # if message['from_user']['username'] != agentname:
    #     user_inform(agentname, city)


def user_inform(agentname, city):
    if "night" in data.keys() and data["night"]:
        # don't send notifications during night
        return
    if agentname in data["counters"]:
        chatid = data["counters"][agentname].get('chatid')
        if chatid is not None:
            send_message(_('Данные по вам изменились:'), chatid, parse_mode="Markdown")
            reply_user_info(chatid, agentname, city)


@restricted
def cmd_send_all(message, city):
    agents_total = 0
    agents_received = 0
    text = message['text'][len('/sendall '):]
    for agentname in data["counters"].keys():
        agents_total += 1
        chat_id = data["counters"][agentname].get('chatid', '')
        if chat_id:
            agents_received += 1
            send_message(_("Агент, вам сообщение от организаторов:\n\n%s"), chat_id, [text])
    reply_to(message, _("Массовое сообщение доставленно %1$d/%2$d агентам") % (agents_received, agents_total))


@restricted
def cmd_softreset(message, city):
    if message['text'] != '/softreset ok':
        reply_to(message, _("Вы правда хотите очистить всю базу, кроме ников?\n\n"
                                "Введите */softreset ok*, если да"), parse_mode="Markdown")
        return
    data["getStart"] = False
    data["getEnd"] = False
    for agentname in data["counters"].keys():
        data["counters"][agentname]['start'] = {}
        data["counters"][agentname]['end'] = {}
    save_data()
    reply_to(message, _("База данных очищена"))


@restricted
def cmd_reset(message, city):
    if message['text'] != '/reset ok':
        reply_to(message, _("Вы правда хотите очистить всю базу?\n\n"
                                "Введите */reset ok*, если да"), parse_mode="Markdown")
        return
    data.clear()
    data["getStart"] = False
    data["getEnd"] = False
    data["counters"] = {}
    data["notify"] = False
    save_data()
    reply_to(message, _("База данных очищена"))


@restricted
def cmd_notify(message, city):
    data["notify"] = not data["notify"]
    save_data()
    if data["notify"]:
        reply_to(message, _("Уведомление агентов включено"))
    else:
        reply_to(message, _("Уведомление агентов выключено"))


@restricted
def cmd_night(message, city):
    if "night" not in data.keys():
        data["night"] = False
    if not data["night"] and (data["getStart"] or data["getEnd"]):
        send_message(_("Нельзя включить ночной режим во время эвента"), message['chat']['id'])
        return
    data["night"] = not data["night"]
    save_data()
    if data["night"]:
        send_message(_("Ночной режим включен"), message['chat']['id'])
    else:
        send_message(_("Ночной режим выключен"), message['chat']['id'])


@restricted
def cmd_agents(message, city):
    txt = _("Зарегистрированные агенты")
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
        fraction = data["counters"][agentname].get("fraction", "-")
        img = fraction_icon(fraction)
        txt += "@%s %s `%s`" % (agentname.replace('_', '\\_'), img, nick.replace('_', '\\_'))
    send_message(txt, message['chat']['id'])


def notify_users(text, curChatId):
    if data["notify"]:
        for agentname in data["counters"].keys():
            send_message(text, data["counters"][agentname]['chatid'])
    else:
        send_message(text, curChatId)


@restricted
def cmd_startevent(message, city):
    data["getStart"] = True
    data["getEnd"] = False
    save_data()
    notify_users(_('Start agent stats are welcome!'), message['chat']['id'])


@restricted
def cmd_endevent(message, city):
    data["getStart"] = False
    data["getEnd"] = True
    save_data()
    notify_users(_('Finish agent stats are welcome!'), message['chat']['id'])


@restricted
def cmd_stop(message, city):
    data["getStart"] = False
    data["getEnd"] = False
    save_data()
    notify_users(_('No more agent stats!'), message['chat']['id'])


@restricted
def cmd_result(message, city):
    delimiter = message['text'][len("/result "):len("/result ") + 1]
    if delimiter == '':
        delimiter = ','
    txt = "TG_nick;Game_nick;Fraction"
    allowed_modes = ["AP", "Level"] + city['modes']
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
    decode_query = {
        "event": 'call.sendRawFile',
        "args": {
            "chatId": message['chat']['id'],
            "body": txt,
            "filename": "result.csv",
        }
    }
    rabbit_send(json.dumps(decode_query))


@restricted
def cmd_resultfev(message, city):
    delimiter = message['text'][len("/resultfev "):len("/resultfev ") + 1]
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
    decode_query = {
        "event": 'call.sendRawFile',
        "args": {
            "chatId": message['chat']['id'],
            "body": txt,
            "filename": "resultfev.csv",
        }
    }
    rabbit_send(json.dumps(decode_query))


def category_name_normalize(name, city):
    allowed_modes = ["AP", "Level"] + city['modes']
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


def cmd_best(message, city):
    allowed_modes = ["AP", "Level"] + city['modes']
    chunks = message['text'].replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) in [2, 3] and (category_name_normalize(chunks[1], city) in allowed_modes))
    amount = int(chunks[2]) if len(chunks) == 3 else 10
    if not is_valid_query:
        send_message(("Неверный формат запроса. Нужно писать:\n"
                      "`/best <category>`\n"
                      "где category принимает значения\n"
                      "" + ', '.join(allowed_modes)), message['chat']['id'], parse_mode="Markdown")
        return
    mode = category_name_normalize(chunks[1], city)
    reply_to(message, _("Вы запросили инфу по %s"), [mode])
    user_data = []
    for agentname in data["counters"].keys():
        if "start" in data["counters"][agentname].keys() and "end" in data["counters"][agentname].keys():
            if mode in data["counters"][agentname]['start'] and mode in data["counters"][agentname]['end']:
                delta = data["counters"][agentname]['end'][mode] - data["counters"][agentname]['start'][mode]
                fraction = data["counters"][agentname].get('fraction', '-')
                user_data.append({"agentname": agentname, "delta": delta, "fraction": fraction})
    user_data.sort(key=itemgetter('delta'), reverse=True)
    body = ''
    for i in range(amount):
        if i < len(user_data):
            user = user_data[i]
            img = fraction_icon(user['fraction'])
            body += "\n#%s %s*%s* - %s" % (i + 1, img, user['agentname'], user['delta'])
    reply_to(message, _('Best %1$s:%2$s'), [mode, body], parse_mode="Markdown")


def cmd_bestn(message, city):
    allowed_modes = ["AP", "Level"] + city['modes']
    chunks = message['text'].replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) in [2, 3] and (category_name_normalize(chunks[1], city) in allowed_modes))
    amount = int(chunks[2]) if len(chunks) == 3 else 10
    if not is_valid_query:
        reply_to(message, (_("Неверный формат запроса. Нужно писать:\n"
                                             "`%1$s`\n"
                                             "где параметр принимает значения\n%2$s")
                                           % ("/best <category>", ', '.join(allowed_modes))), parse_mode="Markdown")
        return
    mode = category_name_normalize(chunks[1], city)
    reply_to(message, _("Вы запросили инфу по %s") % mode)
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
    reply_to(message, txt, parse_mode="Markdown")


def cmd_bestabsolute(message, city):
    allowed_modes = ["AP", "Level"] + city['modes']
    chunks = message['text'].replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) in [2, 3] and (category_name_normalize(chunks[1], city) in allowed_modes))
    amount = int(chunks[2]) if len(chunks) == 3 else 10
    if not is_valid_query:
        reply_to(message, (_("Неверный формат запроса. Нужно писать:\n"
                                             "`%1$s`\n"
                                             "где параметр принимает значения\n%2$s")
                                           % ("/bestabsolute <category>", ', '.join(allowed_modes))), parse_mode="Markdown")
        return
    mode = category_name_normalize(chunks[1], city)
    reply_to(message, _("Вы запросили инфу по %s") % mode)
    user_data = []
    for agentname in data["counters"].keys():
        if "start" in data["counters"][agentname].keys() and "end" in data["counters"][agentname].keys():
            if mode in data["counters"][agentname]['start'] and mode in data["counters"][agentname]['end']:
                value = max(data["counters"][agentname]['end'][mode], data["counters"][agentname]['start'][mode])
                fraction = data["counters"][agentname].get('fraction', '-')
                user_data.append({"agentname": agentname, "value": value, "fraction": fraction})
    user_data.sort(key=itemgetter('value'), reverse=True)
    txt = 'Best absolute %s:' % mode
    for i in range(amount):
        if i < len(user_data):
            user = user_data[i]
            img = fraction_icon(user['fraction'])
            txt += "\n#%s %s*%s* - %s" % (i + 1, img, user['agentname'], user['value'])
    reply_to(message, txt, parse_mode="Markdown")


@restricted
def cmd_clearzero(message, city):
    if message['text'] != '/clearzero ok':
        reply_to(message, _("Вы правда хотите удалить данные c нулевой стартовой статистикой?\n\n"
                                "Введите *%s*, если да") % "/clearzero ok", parse_mode="Markdown")
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
    reply_to(message, _("Удалено %d записей с нулевой стартовой статистикой") % len(agents_to_delete))


@restricted
def cmd_clear(message, city):
    chunks = message['text'].replace("@", "").replace("  ", " ").split(" ")
    is_valid_query = (len(chunks) == 2 and re.fullmatch(r'[a-zA-Z0-9\-_]+', chunks[1]))
    if not is_valid_query:
        send_message(message['chat']['id'], ("Неверный формат запроса. Нужно писать:\n"
                                       "`/clear telegram_nick`\n"), parse_mode="Markdown")
        return
    tg_name = chunks[1]
    if tg_name in data["counters"].keys():
        del data["counters"][tg_name]
        save_data()
        reply_to(message, _("Данные @%s удалены") % tg_name)
    else:
        reply_to(message, _("Бот не располагает данными на @%s") % tg_name)


def cmd_me(message, city):
    tg_name = get_tg_nick(message, city)
    reply_user_info(message['chat']['id'], tg_name, city)


def cmd_clearme(message, city):
    if message['text'] != '/clearme ok':
        reply_to(message, "Вы правда хотите удалить свои данные?\n\n"
                              "Введите */clearme ok*, если да", parse_mode="Markdown")
        return
    tg_name = get_tg_nick(message, city)
    if tg_name in data["counters"].keys():
        del data["counters"][tg_name]
        save_data()
        reply_to(message, _("Ваши данные удалены"))
    else:
        reply_to(message, _("Бот не располагает данными на вас"))


# def cmd_fraction(message, city):
#     chunks = message['text'].replace("  ", " ").split(" ")
#     is_valid_query = (len(chunks) == 2 and re.fullmatch(r'[er]', chunks[1]))
#     if not is_valid_query:
#         reply_to(message, ("Неверный формат запроса. Нужно писать:\n"
#                            "`/fraction e`\n`/fraction r`"), parse_mode="Markdown")
#         return
#     tg_name = get_tg_nick(message, city)
#     fraction = chunks[1]
#     if tg_name not in data["counters"].keys():
#         data["counters"][tg_name] = {"start": {}, "end": {}}
#     data["counters"][tg_name]['fraction'] = fraction
#     save_data()
#     user_save_chatid(tg_name, message['chat']['id'])
#     txt = user_info(tg_name, city)
#     reply_to(message, txt, parse_mode="Markdown")


# def cmd_nick(message, city):
#     chunks = message['text'].replace("@", "").replace("  ", " ").split(" ")
#     is_valid_query = (len(chunks) == 2 and re.fullmatch(r'[a-zA-Z0-9\-_]+', chunks[1]))
#     if not is_valid_query:
#         reply_to(message, (_("Неверный формат запроса. Нужно писать:\n"
#                            "`%s`\n") % '/nick my_game_nick'), parse_mode="Markdown")
#         return
#     tg_name = get_tg_nick(message, city)
#     game_nick = chunks[1]
#     if tg_name not in data["counters"].keys():
#         data["counters"][tg_name] = {"start": {}, "end": {}}
#     data["counters"][tg_name]['Nick'] = game_nick
#     save_data()
#     user_save_chatid(tg_name, message['chat']['id'])
#     txt = user_info(tg_name, city)
#     reply_to(message, txt, parse_mode="Markdown")


def reply_user_info(chatId, username, city):
    allowed_modes = ["AP", "Level"] + city['modes']
    if username not in data["counters"].keys():
        send_message(_('Бот ничего не знает по вам'), chatId, parse_mode="Markdown")
        return

    user_data = data["counters"][username]
    placeholders = [
        username.replace('_', '\\_'),
    ]

    game_nick = user_data.get("Nick", "-")
    if game_nick != '-':
        placeholders.append(game_nick.replace('_', '\\_'))
    fraction = user_data.get("fraction", "")
    placeholders.append(full_fraction_name(fraction))

    start_values = ''
    end_values = ''
    for mode in allowed_modes:
        value = user_data["start"].get(mode, "-")
        start_values += "\n_%s:_ *%s*" % (mode, value)
    placeholders.append(start_values)
    if "end" in user_data.keys() and len(user_data['end'].keys()) > 0:
        for mode in allowed_modes:
            value = user_data["end"].get(mode, "-")
            end_values += "\n_%s_: *%s*" % (mode, value)
            if mode in user_data["start"].keys() and mode in user_data["end"].keys():
                delta = (user_data["end"][mode] - user_data["start"][mode])
                end_values += " (+%s)" % delta

    if end_values:
        txt = _("Ник телеги: @%s\n"
                "Ник в игре: %s\n"
                "Фракция: %s\n"
                "== Стартовые показатели:" 
                "%s\n"
                "== Финишные показатели:"
                "%s")
        placeholders.append(end_values)
    else:
        txt = _("Ник телеги: @%s\n"
                "Ник в игре: %s\n"
                "Фракция: %s\n"
                "== Стартовые показатели:\n"
                "%s")
    send_message(txt, chatId, placeholders, parse_mode="Markdown")
    # reply_to(message, txt, parse_mode="Markdown")


def get_tg_nick(message, city):
    tg_nick = message['from'].get('username', None)
    if tg_nick is None:
        tg_nick = '#' + str(message['chat']['id'])
    return tg_nick


# @message_handler(func=lambda message: True, content_types=["text"])
def process_msg(message, city):
    if message['chat']['id'] < 0:
        return
    tg_name = get_tg_nick(message, city)
    # decode_query = {
    #     "event": 'core.messageIn',
    #     "text": message['text'],
    #     "msgid": message.message_id,
    #     "chatid": message['chat']['id'],
    #     "tg_name": tg_name
    # }
    # rabbit_send(json.dumps(decode_query))

    if len(message['text']) > 100:
        return process_prime_tab_separated_text(message, city)
    if message['isAdmin']:
        user_tg_name = message['text'].replace('@', '')
        if user_tg_name in data["counters"].keys():
            reply_user_info(message['chat']['id'], user_tg_name, city)
            # reply_to(message, txt, parse_mode="Markdown")
        elif user_tg_name[0] != '/':
            send_message(_('That user is not found in database'), message['chat']['id'])
            # txt = "Такой пользователь не найден в базе"
            # bot.send_message(message['chat']['id'], txt, parse_mode="Markdown")


def send_message(text, chatid, placeholders=None, parse_mode=None):
    decode_query = {
        "event": 'call.translateAndSend',
        "args": {
            "chatId": chatid,
            "text": text,
            "placeholders": placeholders,
            "formatted": (parse_mode is not None),
        }
    }
    rabbit_send(json.dumps(decode_query))


def process_prime_tab_separated_text(message, city):
    msgid = message['message_id']
    chatid = message['chat']['id']

    chunks = message['text'].split("\n")
    if len(chunks) != 2:
        reply_to(message, _("Не могу разобрать выгрузку! Возможно к тексту попала приписка Forwarded?"))
        return
    title = chunks[0]
    titles = parse_title(title)
    values = chunks[1]

    regexp = re.compile('(.*)\s(\S+)\s(Enlightened|Resistance)\s(\d\d\d\d-\d\d-\d\d)\s(\d\d:\d\d:\d\d)\s([\s\d]+)')
    found = re.fullmatch(regexp, values)

    if not found:
        # bot.forward_message(CHAT_FAIL, chatid, msgid)
        reply_to(message, _("Не могу разобрать выгрузку! Отправьте пожалуйста скрин картинкой"))
        return

    time_span = found[1]
    nick = found[2]
    fraction = 'e' if found[3] == 'Enlightened' else 'r'
    date = found[4]
    time = found[5]
    rest = found[6].split(' ')
    rest2 = [time_span, nick, fraction, date, time] + rest

    if time_span in ['ЗА МЕСЯЦ', 'MONTH']:
        reply_to(message, _('Вы прислали месячную стату. А нужно "за всё время"'))
        return

    if time_span in ['ЗА НЕДЕЛЮ', 'WEEK']:
        reply_to(message, _('Вы прислали недельную стату. А нужно "за всё время"'))
        return

    if time_span in ['СЕЙЧАС', 'NOW'] or 'ActivePortalsOwned' in titles:
        reply_to(message, _('Вы прислали дневную стату. А нужно "за всё время"'))
        return

    if len(titles) != len(rest2):
        LOG.info(titles)
        LOG.info(rest2)
        # bot.forward_message(CHAT_FAIL, chatid, msgid)
        reply_to(message, _("Не могу разобрать выгрузку - обнаружен неизвестный боту параметр. Отправьте пожалуйста скрин картинкой"))
        return

    decoded = {}
    for i in range(len(rest2)):
        val = rest2[i]
        if re.fullmatch(r'\d+', val):
            val = int(val)
        decoded[titles[i]] = val

    LOG.info('decoded ' + str(decoded))

    agentname = get_tg_nick(message, city)
    if 'forward_from' in message:
        if message['isAdmin'] or (agentname == message['forward_from'].username):
            agentname = message['forward_from'].username
    else:
        user_save_chatid(agentname, message['chat']['id'])

    if data["getStart"]:
        datakey = "start"
        if 'start' in data["counters"][agentname].keys():
            if 'LifetimeAP' in data["counters"][agentname]['start']:
                if decoded['LifetimeAP'] > data["counters"][agentname]['start']['LifetimeAP']:
                    datakey = "end"
    elif data["getEnd"]:
        datakey = "end"
    else:
        datakey = "pre"

    if not data["getStart"] and not data["getEnd"]:
        txt = _("Регистрация на эвент ещё не началась. На твоей выгрузке я вижу вот что:\n")
        d = decoded
        fraction = full_fraction_name(d['Fraction'])
        txt += "Fraction *%s*\nAP *%s*\nLvl *%s*\n" % (
            fraction, d["AP"], d["Level"])
        for mode in city['modes']:
            if mode in d.keys():
                txt += "%s *%s*\n" % (mode, d[mode])
        reply_to(message, txt, parse_mode="Markdown")
        return
    data["counters"][agentname]['Nick'] = decoded['Nick']
    data["counters"][agentname]['fraction'] = decoded['Fraction']
    data["counters"][agentname][datakey].update(decoded)
    save_data()
    user_inform(agentname, city)
    # bot.forward_message(CHAT_OK, chatid, msgid)
    # bot.send_message(CHAT_OK, "Parsed: " + str(decoded))


def reply_to(msg, text, placeholders=None, parse_mode=None):
    send_message(text, msg['chat']['id'], placeholders, parse_mode=parse_mode)


def parse_title(title):
    title = str(title).replace('Time Span', 'TimeSpan')
    title = str(title).replace('Agent Name', 'Nick')
    title = str(title).replace('Agent Faction', 'Fraction')
    title = str(title).replace('Date (yyyy-mm-dd)', 'Date')
    title = str(title).replace('Time (hh:mm:ss)', 'Time')
    title = str(title).replace('Lifetime AP', 'LifetimeAP')
    title = str(title).replace('Current AP', 'AP')
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
    title = str(title).replace('OPR Live Events', 'OPRLive')
    title = str(title).replace('Umbra: Unique Resonator Slots Deployed', 'Umbra')
    ans = title.split(' ')
    ans.pop()
    return ans


# @message_handler(func=lambda message: True, content_types=["photo"])
# def process_photo(message, city):
#     return
    # agentname = get_tg_nick(message)
    # if message['forward_from']:
    #     if (message['isAdmin']) or (agentname == message['forward_from'].username):
    #         agentname = message['forward_from'].username
    # user_save_chatid(agentname, message['chat']['id'])
    # file_id = message.photo[-1].file_id
    # file_info = bot.get_file(file_id)
    # downloaded_file = bot.download_file(file_info.file_path)
    # filename = agentname + "_"
    # if data["getStart"]:
    #     datakey = "start"
    # elif data["getEnd"]:
    #     datakey = "end"
    # else:
    #     datakey = "pre"
    # postfix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    # filename += datakey + "_" + str(postfix) + ".jpg"
    # LOG.info(agentname + ' <- IMG ' + filename)
    # with open("/Screens/" + filename, "wb") as new_file:
    #     new_file.write(downloaded_file)
    # decode_query = {}
    # decode_query['img'] = filename
    # decode_query['msgid'] = message.message_id
    # decode_query['chatid'] = message['chat']['id']
    # decode_query['datakey'] = datakey
    # decode_query['agentname'] = agentname
    # rabbit_send(json.dumps(decode_query))


def full_fraction_name(short_name):
    if short_name == 'e':
        return 'Enlight'
    elif short_name == 'r':
        return 'Resist'
    else:
        return 'Unknown'


def _(str):
    return str


def on_message(channel, method_frame, header_frame, body):
    try:
        LOG.info('{Rabbit} <= %s', body)
        decoded = json.loads(body)
        if 'event' in decoded.keys():
            # if decoded['event'] == 'call.telegramSend':
                # args = decoded['args']
                # bot.send_message(args['chatId'], args['text'])
            if decoded['event'] == 'core.messageIn':
                raw_msg = decoded['rawMsg']
                chunks = raw_msg['text'].replace("  ", " ").split(" ")
                cmd_name = raw_msg['text'].replace("  ", " ").split(" ")[0]
                city = decoded['city']
                if cmd_name == '/ping':
                    send_message(_('Pong from %s'), decoded['chatid'], ['bot'])
                elif cmd_name == '/best':
                    cmd_best(raw_msg, city)
                elif cmd_name == '/bestabsolute':
                    cmd_bestabsolute(raw_msg, city)
                elif cmd_name == '/bestn':
                    cmd_bestn(raw_msg, city)
                elif cmd_name == '/clear':
                    cmd_clear(raw_msg, city)
                elif cmd_name == '/clearme':
                    cmd_clearme(raw_msg, city)
                elif cmd_name == '/clearzero':
                    cmd_clearzero(raw_msg, city)
                elif cmd_name == '/endevent':
                    cmd_endevent(raw_msg, city)
                # elif cmd_name == '/fraction':
                #     cmd_fraction(raw_msg, city)
                elif cmd_name == '/help':
                    cmd_help(raw_msg, city)
                elif cmd_name == '/me':
                    cmd_me(raw_msg, city)
                # elif cmd_name == '/nick':
                #     cmd_nick(raw_msg, city)
                elif cmd_name == '/night':
                    cmd_night(raw_msg, city)
                elif cmd_name == '/notify':
                    cmd_notify(raw_msg, city)
                elif cmd_name == '/reset':
                    cmd_reset(raw_msg, city)
                elif cmd_name == '/result':
                    cmd_result(raw_msg, city)
                elif cmd_name == '/resultfev':
                    cmd_resultfev(raw_msg, city)
                elif cmd_name == '/send_all':
                    cmd_send_all(raw_msg, city)
                elif cmd_name == '/set':
                    cmd_set(raw_msg, city)
                elif cmd_name == '/softreset':
                    cmd_softreset(raw_msg, city)
                elif cmd_name == '/startevent':
                    cmd_startevent(raw_msg, city)
                elif cmd_name == '/stop':
                    cmd_stop(raw_msg, city)
                else:
                    process_msg(raw_msg, city)
            else:
                LOG.warning('unknown event ' + decoded['event'])
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            return
        msgid = decoded['msgid']
        chatid = decoded['chatid']
        datakey = decoded['datakey']
        agentname = decoded['agentname']
        if not data["getStart"] and not data["getEnd"]:
            txt = _("Регистрация на эвент ещё не началась. На твоём изображении я вижу вот что:\n")
            if decoded["success"]:
                # txt += "\n_%s_: *%s*" % (mode, value)
                d = decoded
                fraction = full_fraction_name(d['fraction'])
                txt += "Fraction *%s*\nAP *%s*\nLvl *%s*\n%s *%s*" % (
                    fraction, d["AP"], d["Level"], d["mode"], d[d["mode"]])
            else:
                txt += _("Данные с изображения распарсить не удалось")
            send_message(txt, chatid, parse_mode="Markdown")
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            return
        if "success" in decoded.keys() and decoded["success"]:
            # if decoded.get('mode') in MODES:
                if decoded['fraction']:
                    data["counters"][agentname]['fraction'] = decoded['fraction']
                data["counters"][agentname][datakey].update(decoded)
                save_data()
                # user_inform(agentname, city)
                # bot.forward_message(CHAT_OK, chatid, msgid)
                # send_message("Агент %s, AP %s, %s %s" % (
                #    agentname, decoded["AP"], decoded["mode"], decoded[decoded["mode"]]), CHAT_OK)
            # else:
            #     send_message(_("Вы прислали скрин из неактивной категории *%1$s*. Пришлите вместо него *%2$s*") %
            #                  (decoded.get('mode'), ', '.join(MODES)), chatid, parse_mode="Markdown")
        else:
            # bot.forward_message(CHAT_FAIL, chatid, msgid)
            send_message(_("Не могу разобрать скрин! Отправьте другой, или зарегистрируйтесь у оргов вручную"), chatid)
    except Exception as e:
        LOG.error('Exception: ' + str(e), exc_info=e)
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def user_save_chatid(agentname, chatid):
    if chatid > 0:
        if agentname not in data["counters"].keys():
            data["counters"][agentname] = {"pre": {}, "start": {}, "end": {}}
            save_data()
        if data["counters"][agentname].get('chatid') != chatid:
            data["counters"][agentname]['chatid'] = chatid
            save_data()


def rabbit_send(msg):
    LOG.info('{Rabbit} => %s', msg)
    ev = json.loads(msg)
    event_route = ev['event'] if "event" in ev else 'parseRequest'
    rabbit_channel.basic_publish('topic', event_route, msg)
    connection.process_data_events()
    connection.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    LOG = logging.getLogger(__name__)
    credentials = pika.PlainCredentials('rabbitmq', 'rabbitmq')
    parameters = pika.ConnectionParameters("rabbit", 5672, '/', credentials, heartbeat=None, frame_max=20000)
    connection = pika.BlockingConnection(parameters)
    rabbit_channel = connection.channel()
    rabbit_channel.basic_qos(prefetch_count=1)
    rabbit_channel.exchange_declare(exchange='topic', exchange_type='topic', durable=True)
    rabbit_channel.queue_declare(queue='bot', durable=True)
    rabbit_channel.queue_bind('bot', 'topic', 'parseResult')
    rabbit_channel.queue_bind('bot', 'topic', 'core.messageIn')
    rabbit_channel.basic_consume('bot', on_message)
    try:
        rabbit_channel.start_consuming()
    except KeyboardInterrupt:
        rabbit_channel.stop_consuming()
