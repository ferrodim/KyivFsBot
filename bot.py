#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
from functools import wraps
import pytesseract
import telebot
import json
import datetime
import re
import csv
import difflib
import random
import string
from config import ADMINS, MODES, API_TOKEN, WELCOME, CHAT_OK, CHAT_FAIL

print("restart")
print(WELCOME)

bot = telebot.TeleBot(API_TOKEN)
try:
    datafile = open("base.txt", "r")
    data = json.load(datafile)
except FileNotFoundError:
    data = {}
    datafile = open("base.txt", "w")
    json.dump(data, datafile, ensure_ascii=False)
if not "welcome" in data.keys():
    data["welcome"] = u"hello"
if not "getStart" in data.keys():
    data["getStart"] = False
if not "getEnd" in data.keys():
    data["getEnd"] = False
if not "okChat" in data.keys(): 
    data["okChat"] = CHAT_OK
if not "failChat" in data.keys():
    data["failChat"] = CHAT_FAIL
if not "reg" in data.keys():
    data["reg"] = {}
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

def strDiff(str1:str, str2:str):
    d = difflib.ndiff(str1, str2)
    diffs = []
    for dd in d:
        if dd[0] in ["+", "-"]:
            diffs.append(dd)
    #print('diffs', diffs);
    return len(diffs) < len(str2) - 4


def returnVal(ap:int, name:str, value:str):
    kmregexp = re.compile(r"([0-9]+)k(m|rn|n)")
    numregexp = re.compile(r"^([0-9]+)$")
    print('returnVal', name)
    global MODES
    if strDiff(name, "Trekker") and "Trekker" in MODES:
        match = kmregexp.match(value)
        if match:
            return {"success": True, "AP": ap, "Trekker": int(match.group(1)), "mode": "Trekker"}
    if strDiff(name, "Builder") and "Builder" in MODES:
        match = numregexp.match(value)
        if match:
            return {"success": True, "AP": ap, "Builder": int(value), "mode": "Builder"}
    if strDiff(name, "Purifier") and "Purifier" in MODES:
        match = numregexp.match(value)
        if match:
            return {"success": True, "AP": ap, "Purifier": int(value), "mode": "Purifier"}
    return False


def colorDiff(px:tuple, color:tuple):
    return abs(px[0]-color[0]) + abs(px[1]-color[1]) + abs(px[2]-color[2])


def find_lines(pixels:tuple, width:int, rect:tuple, colors:list, threshhold:int, minWidth:int=1, findCount:int=0, average:bool=True, horizontal:bool=True):
    w = rect[2]-rect[0]
    h = rect[3]-rect[1]
    xRange = w if horizontal else h
    yStart = rect[1] if horizontal else rect[0]
    yEnd = rect[3] if horizontal else rect[2]
    pxDiff = 1 if horizontal else w
    results = []
    last = 0
    concurrent = 0
    for y in range(yStart, yEnd):
        lineError = 0
        if horizontal:
            currPx = y * width + rect[0]
        else:
            currPx = y + rect[1] * width
        process = True
        for x in range(xRange):
            if process:
                diffs = tuple(colorDiff(pixels[currPx], color) for color in colors)
                currPx += pxDiff
                lineError += min(diffs)
                if not average:
                    if min(diffs) > threshhold:
                        process = False
        if process:
            lineError /= w
            if lineError < threshhold:
                concurrent += 1
                if concurrent >= minWidth and y - last > minWidth * 3:
                    results.append(y)
                    last = y
                    if findCount and (len(results) >= findCount):
                        return results
            else:
                concurrent = 0
        else:
            concurrent = 0
    return results


def parse_image(filename:str):
    debugLevel = 0
    ap = 0
    trekker = 0
    apregexp = re.compile(r"([0-9]+)A[PF]")
    img = Image.open(filename)
    yellow = (255, 243, 140)
    green = (0, 134, 123)
    marble = (20, 175, 165)
    redactLine = (0, 186, 181)
    pink = (188, 50, 124)
    primeBack = (11, 18,36)
    pxls = tuple(img.getdata())

    #Search for AP line
    APLines = find_lines(pxls, img.width, (int(img.width * 0.3), int(img.height * 0.075), int(img.width * 0.9), int(img.height * 0.4)), [yellow, green], 70, 3, 1)
    APLine = APLines[0] if len(APLines) else False

    if APLine: #We found AP line - Scanner "Redacted" mode
        redactLines = find_lines(pxls, img.width, (int(img.width * 0.1), int(img.height * 0.25), int(img.width * 0.9), int(img.height * 0.95)), [redactLine], 200, 1)
        if debugLevel >= 2:
            print(redactLines)
        if len(redactLines) > 1: #Found top and bottom border of opened medal
            redactVLines = find_lines(pxls, img.width, (0, redactLines[0], img.width, redactLines[1]), [redactLine], 150, 1, 0, True, False)
            if debugLevel >= 2:
                print(redactVLines)
            if len(redactVLines) in (2,3): #found left and right
                #Extract medal name to IMG
                medalName=img.crop((int(redactVLines[1] * 0.25 + redactVLines[0] * 0.75) + 10, redactLines[0] + 5, int(redactVLines[1] * 0.9 + redactVLines[0] * 0.1), int(redactLines[0] * 0.65 + redactLines[1] * 0.35)))
                if debugLevel >= 1:
                    medalName.save("tables/" + filename + "_name.png")
                #Find first black line above medal value
                blackLines=find_lines(pxls, img.width, (redactVLines[0] + 5, int(redactLines[0] * 0.6 + redactLines[1] * 0.4), int(redactVLines[0] / 2 + redactVLines[1] / 2), int(redactLines[0] * 0.35 + redactLines[1] * 0.65)), [(0,0,0)], 100, 1, 1, False)
                if len(blackLines): #Found
                    medalValRect = [redactVLines[0] + 10, blackLines[0], int(redactVLines[1] * 0.3 + redactVLines[0] * 0.7), int(redactLines[0] * 0.4 + redactLines[1] * 0.6)]
                    #Crop from top
                    top = medalValRect[1]
                    currpx = img.width * top + int(medalValRect[0] / 2 + medalValRect[2] / 2)
                    while top < medalValRect[3] and pxls[currpx][0] + pxls[currpx][1] + pxls[currpx][2] < 50:
                        currpx += img.width
                        top +=1
                    medalValRect[1] = top + 2

                    #Crop from bottom
                    bottom = medalValRect[3]
                    currpx = img.width * bottom + int(medalValRect[0] / 2 + medalValRect[2] / 2)
                    while bottom > top and pxls[currpx][0] + pxls[currpx][1] + pxls[currpx][2] < 50:
                        currpx -= img.width
                        bottom -=1
                    medalValRect[3] = bottom - 2

                    #Extract medal value to IMG
                    medalValue=img.crop(medalValRect)
                    if debugLevel >= 1:
                        medalValue.save("tables/" + filename + "_val.png")

                    #Find black dot before AP line (left AP border)
                    left = int(img.width / 2)
                    currpx = img.width * APLine + left
                    while left > 0 and pxls[currpx][0] + pxls[currpx][1] + pxls[currpx][2] > 150:
                        currpx -= 1
                        left -= 1

                    #Find first black line after AP line
                    top = 0
                    currpx = img.width * APLine + left + 1
                    while APLine + top < img.height and pxls[currpx][0] + pxls[currpx][1] + pxls[currpx][2] > 150:
                        currpx += img.width
                        top += 1

                    #Extract AP to file (height == height of medal value)
                    apImg = img.crop((left - 5, APLine + top, img.width, APLine + medalValue.height + 5))
                    if debugLevel >= 1:
                        apImg.save("tables/" + filename + "_ap.png")

                    #Filter out non-yellow pixels
                    pixels = apImg.getdata()
                    apImg.putdata([px if px[0] > px[2] else (0,0,0) for px in pixels])
                    if debugLevel >= 1:
                        apImg.save("tables/" + filename + "_ap_filter.png")
                    #OCR, replace some letters
                    ap = pytesseract.image_to_string(apImg).replace("I", "1").replace("L", "1").replace("l", "1").replace("S", "6").replace("B", "8").replace("E", "8").replace(".", "").replace(",", "").replace(" ", "").replace("[", "1").replace("]", "1").replace("{", "1").replace("}", "1").replace("H", "11").replace("O", "0").replace("D", "0").replace("\"", "11")
                    if debugLevel >= 2:
                        print("AP:", ap)
                    match = apregexp.match(ap)
                    if match: #Got AP!
                        ap = int(match.group(1))
                        #OCR name and value, replace letters in value
                        name = pytesseract.image_to_string(medalName, "eng").split("\n")[0].replace("ﬁ","fi")
                        if name in ["Buﬂder", "Bquer"]:
                            name = "Builder"
                        value = pytesseract.image_to_string(medalValue, "eng")
                        value = value.replace("I", "1").replace("L", "1").replace("l", "1").replace("S", "6").replace("B", "8").replace("E", "8").replace(".", "").replace(",", "").replace(" ", "").replace("[", "1").replace("]", "1").replace("{", "1").replace("}", "1").replace("H", "11").replace("O", "0").replace("D", "0")
                        if debugLevel >= 2:
                            print("Name:", name, "Value:", value)
                        #Check if everything is OK
                        ret = returnVal(ap, name, value)
                        if ret != False:
                            if debugLevel >= 1:
                                img.save("results/ok/"+filename)
                            return ret
    else: #No AP line. Prime?
        #Find pink lines (1 - above AP, 2 - in medal)
        pinkLines=find_lines(pxls, img.width, (int(img.width * 0.3), 0, int(img.width * 0.7), int(img.height * 0.7)), [pink], 180, 1, 2)
        if debugLevel >= 2:
            print(pinkLines)
        if len(pinkLines) == 2: #Found
            #Search for empry line after AP
            primeBacks=find_lines(pxls, img.width, (int(img.width * 0.25), pinkLines[0] + 40, int(img.width * 0.98), pinkLines[1]), [primeBack], 50, 1, 1, False)
            if debugLevel >= 2:
                print(primeBacks)
            if len(primeBacks) == 1:
                #Main height parameter
                primeHeight = primeBacks[0] - pinkLines[0]
                #Extract AP to IMG
                primeAPImg = img.crop((int(img.width * 0.25), pinkLines[0] + 10, img.width, primeBacks[0]))
                if debugLevel >= 1:
                    primeAPImg.save("tables/" + filename + "_ap.png")

                #Filter out second part (" / 40 000 000"), nickname and level
                pixels = primeAPImg.getdata()
                primeAPImg.putdata([px if abs(px[0] - 159) + abs(px[1] - 164) + abs(px[2] - 230) < 120 else (0,0,0) for px in pixels])
                if debugLevel >= 1:
                    primeAPImg.save("tables/" + filename + "_ap_filter.png")

                #OCR AP, replace letters
                ap = pytesseract.image_to_string(primeAPImg, "eng").replace("I", "1").replace("L", "1").replace("l", "1").replace("B", "8").replace("E", "8").replace(".", "").replace(",", "").replace(" ", "").replace("/", "").replace("O", "0").replace("D", "0")
                if debugLevel >= 2:
                    print("AP:", ap)
                match = apregexp.match(ap)
                if match: #Got AP!
                    ap = int(match.group(1))
                    #Get medal part
                    primeTRImg = img.crop((int(img.width / 4), pinkLines[1] - int(primeHeight / 2), int(img.width * 3 / 4), pinkLines[1] + int(primeHeight * 2 / 3)))
                    if debugLevel >= 1:
                        primeTRImg.save("tables/" + filename + "_val.png")
                    #OCR, get name and value, replace letters in val
                    trLines = pytesseract.image_to_string(primeTRImg, "eng").split("\n")
                    value = trLines[0].replace("I", "1").replace("L", "1").replace("l", "1").replace("B", "8").replace("E", "8").replace(".", "").replace(",", "").replace(" ", "").replace("[", "1").replace("]", "1").replace("{", "1").replace("}", "1").replace("H", "11").replace("O", "0").replace("D", "0")
                    name = trLines[len(trLines) - 1]
                    if name in ["Buﬂder", "Bquer"]:
                        name = "Builder"
                    if debugLevel >= 2:
                        print("Name:", name, "Value:", value)
                    #Check if everything is OK
                    ret = returnVal(ap, name, value)
                    if ret != False:
                        if debugLevel >= 1:
                            img.save("results/ok/"+filename)
                        return ret
    if debugLevel >= 1:
        img.save("results/bad/"+filename)
    return {"filename": filename, "success": False}


def restricted(func):
    @wraps(func)
    def wrapped(message, *args, **kwargs):
        if message.from_user.username not in ADMINS:
            bot.reply_to(message, ("А ну кыш отсюда!"))
            return
        return func(message, *args, **kwargs)
    return wrapped


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, (data["welcome"]))


@bot.message_handler(commands=["help"])
def send_welcome(message):
    bot.reply_to(message, ("username - (for admins) Get userinfo\n/startevent - (for admins) Begin taking start screenshots\n/endevent - (for admins) Begin taking final screenshots\n/reset - (for admins) Clear all data and settings\n/result - (for admins) Get result table file\n/stop - (for admins) Stop taking events\n/setwelcome - (for admins) Set welcome message"))


@bot.message_handler(commands=["setwelcome"])
@restricted
def setwelcome(message):
    data["welcome"] = message.text[str(message.text + " ").find(" "):]
    save_data()
    bot.send_message(message.chat.id, ("Обновил приветствие"))

@bot.message_handler(commands=["set"])
@restricted
def setCounter(message):
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
    #print(chunks)
    if agentname in data["counters"].keys():
        txt = "Досье на: @%s\n"%(agentname)
        txt += user_info(agentname)
    else:
        txt = "Такой пользователь не найден в базе"
    bot.send_message(message.chat.id, (txt))
    #data["welcome"] = message.text[str(message.text + " ").find(" "):]
    #bot.send_message(message.chat.id, ("Обновил приветствие"))


@bot.message_handler(commands=["reset"])
@restricted
def forget(message):
    data.clear()
    data["regchat"] = 0
    data["getStart"] = False
    data["getEnd"] = False
    data["okChat"] = CHAT_OK
    data["failChat"] = CHAT_FAIL
    data["reg"] = {}
    data["counters"] = {}
    data["welcome"] = WELCOME
    save_data()
    bot.reply_to(message, ("Всё, я всё забыл :)"))


@bot.message_handler(commands=["reg"])
@restricted
def addreg(message):
    names = message.text.replace("@", "").split(" ")
    if (len(names) == 3):
        data["reg"][names[2].lower()] = names[1]
        save_data()
        bot.reply_to(message, ("Добавил агента %s с телеграм-ником %s"%(names[1], names[2].lower())))
        return
    bot.reply_to(message, ("Формат: /reg agentname telegramname"))
    return


@bot.message_handler(commands=["startevent"])
@restricted
def setstart(message):
    data["getStart"] = True
    data["getEnd"] = False
    save_data()
    bot.send_message(message.chat.id, ("Принимаю скрины!"))


@bot.message_handler(commands=["endevent"])
@restricted
def setend(message):
    data["getStart"] = False
    data["getEnd"] = True
    save_data()
    bot.send_message(message.chat.id, ("Принимаю скрины!"))


@bot.message_handler(commands=["stop"])
@restricted
def setstop(message):
    data["getStart"] = False
    data["getEnd"] = False
    save_data()
    bot.send_message(message.chat.id, ("Не принимаю скрины!"))


@bot.message_handler(commands=["result"])
@restricted
def getresult(message):
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
    resultfile = open("result.csv", "w")
    resultfile.write(txt)
    resultfile.close()
    resultfile = open("result.csv", "rb")
    bot.send_document(message.chat.id, resultfile)
    resultfile.close()


@bot.message_handler(commands=["me"])
def get_my_info(message):
    txt = user_info(message.from_user.username);
    bot.send_message(message.chat.id, (txt))

@bot.message_handler(commands=["clearme"])
@restricted
def loadreg(message):
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
    #print(message.chat.id)
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
    username = message.chat.username
    if message.forward_from:
        username = message.forward_from.username
    #if not data["getStart"] and not data["getEnd"]:
    #    bot.send_message(message.chat.id, ("Я вообще-то сейчас не принимаю скрины!"))
    #    return
    print("username", username)
    if username.lower() in data["reg"].keys():
        agentname = data["reg"][username.lower()]
    else:
        agentname = username
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
