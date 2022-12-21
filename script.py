# Работа с ботом
import telebot
from telebot import types
# Работа с определением тональности текста
from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel
# Работа с определением погоды
from pyowm import OWM
# Работа с передачей и отрисовкой картинок
from PIL import Image
# Работа с переводом слов
from telebot.types import InputFile
from translate import Translator
# Работа с графиками
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
# Работа с конфигом, чтобы держать токены в безопасности
# Работа с запросами
import requests
# Работа с операционной системой
import os
import random
from datetime import datetime

# Получение наиболее вероятного предикта по тональности
def get_biggest_tone_item(tone):
    result = {}
    max_tone = -1
    for key, value in tone.items():
        if value > max_tone:
            result = (key, value)
            max_tone = value
    return result


# Получение информации о тональности текста (по предложениям)
def get_text_tone(sentences):
    tokenizer = RegexTokenizer()
    model = FastTextSocialNetworkModel(tokenizer=tokenizer)
    tones = model.predict(sentences, k=2)
    result = []
    i = 0
    for tone in tones:
        predict = get_biggest_tone_item(tone)
        result.append({'text': sentences[i], 'tone': tone, 'predict': predict})
        i += 1
    return result


def get_weather_icon_url(weather):
    try:
        icon = weather.weather_icon_name
        return f'http://openweathermap.org/img/wn/{icon}@2x.png'
    except:
        return None


def get_weather_info_str(weather):
    status = ''
    wind = ''
    humidity = ''
    temperature = ''
    clouds = ''
    pressure = ''

    translator = Translator(to_lang="ru")

    try:
        status_rus = translator.translate(weather.detailed_status).capitalize()
        status = f'Погода: {status_rus}'
    except:
        pass

    try:
        wind_speed = weather.wind()['speed']
        wind = f'\nСкорость ветра: {wind_speed} м/с'
    except:
        pass

    try:
        humidity = f'\nВлажность: {weather.humidity}%'
    except:
        pass

    try:
        temp = weather.temperature('celsius')['temp']
        temperature = f'\nТемпература: {temp} °C'
    except:
        pass

    try:
        clouds = f'\nОблачность: {weather.clouds}%'
    except:
        pass

    try:
        press = weather.pressure['press']
        pressure = f'\nДавление: {press} Па'
    except:
        pass

    return status + wind + humidity + temperature + clouds + pressure


def get_weather(location):
    result = {}
    try:
        weather = weather_manager.weather_at_place(location).weather
        result['result_str'] = get_weather_info_str(weather)
        icon_url = get_weather_icon_url(weather)
        if icon_url != None:
            result['icon_url'] = icon_url
    except:
        result['result_str'] = 'Не удалось найти информацию о погоде в данной локации, попробуй еще раз.'
    return result

def get_forecast_weather_str(weather):
  day = ''
  status = ''
  temperature = ''

  translator = Translator(to_lang="ru")

  try:
    dt = datetime.fromtimestamp(weather.ref_time)
    day = f'Дата: {dt.date()}'
  except:
    pass

  try:
    status_rus = translator.translate(weather.detailed_status).capitalize()
    status = f'\nПогода: {status_rus}'
  except:
    pass

  try:
    temp = weather.temperature('celsius')
    max = temp['max']
    min = temp['min']
    temperature = f'\nТемпература: макс. {max}°C, мин. {min}°C'
  except:
    pass

  return day + status + temperature

def get_forecast(location):
  try:
    loc = weather_manager.weather_at_place(location).location
    location_str = f'Координаты: широта {loc.lat}, долгота {loc.lon}\n'
    forecast = weather_manager.one_call(loc.lat, loc.lon).forecast_daily
    days = list(map(lambda w: get_forecast_weather_str(w), forecast))
    result_str = location_str
    for day in days:
      result_str += '\n' + day + '\n'
    return result_str
  except:
    return 'Не удалось найти информацию о погоде в данной локации, попробуй еще раз.'


def get_ticker(ticker):
    result = {}
    result["ticker"] = str(ticker)
    stock = yf.Ticker(str(ticker))
    hist = stock.history(period="1y")
    if len(hist.index) > 20:
        graph = make_subplots(specs=[[{"secondary_y": True}]])
        graph.add_trace(go.Candlestick(x=hist.index,
                                       open=hist['Open'],
                                       high=hist['High'],
                                       low=hist['Low'],
                                       close=hist['Close'],
                                       ))
        graph.update_layout(xaxis_rangeslider_visible=False)
        if not os.path.exists("images"):
            os.mkdir("images")
        graph.to_image()
        graph.write_image(f"images/{ticker}.png")
        work = True
    else:
        work = False
    result["work"] = bool(work)
    return result

tictactoe = [
    ['-', '-', '-'],
    ['-', '-', '-'],
    ['-', '-', '-']
]

def start_game(id):
    global game_end
    game_end = False

    clear_game_field()

    keyboard = get_game_field()
    bot.send_message(id, 'Начинай игру!', reply_markup=keyboard)


def ans(res):
    try:
        global game_end

        data = res.data
        user_id = res.from_user.id
        message_id = res.message.id

        if data == 'restart':
            clear_game_field()
            game_end = False
            keyboard = get_game_field()
            bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Твой ход!", reply_markup=keyboard)
        elif data == 'finish':
            game_end = True
            clear_game_field()
            bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Игра завершена!")
        else:
            if game_end: return

            set_user_ans(data)

            if is_user_won():
                keyboard = get_game_field()
                bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Вы выйграли!", reply_markup=keyboard)
                game_end = True
                return

            if is_game_finished():
                keyboard = get_game_field()
                bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Игра завершилась ничьей!", reply_markup=keyboard)
                game_end = True
                return

            set_bot_ans()

            if is_bot_won():
                keyboard = get_game_field()
                bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Вы проиграли!", reply_markup=keyboard)
                game_end = True
                return

            keyboard = get_game_field()
            bot.edit_message_text(chat_id=user_id, message_id=message_id, text="Твой ход!", reply_markup=keyboard)
    except:
        print("Ячейка уже занята!")


def is_user_won():
    return is_someone_won("❌")


def is_bot_won():
    return is_someone_won("⭕")


def is_someone_won(char):
    return (
        # По горизонтали
        (tictactoe[0][0] == tictactoe[0][1] == tictactoe[0][2] == char) or
        (tictactoe[1][0] == tictactoe[1][1] == tictactoe[1][2] == char) or
        (tictactoe[2][0] == tictactoe[2][1] == tictactoe[2][2] == char) or
        # По вертикали
        (tictactoe[0][0] == tictactoe[1][0] == tictactoe[2][0] == char) or
        (tictactoe[0][1] == tictactoe[1][1] == tictactoe[2][1] == char) or
        (tictactoe[0][2] == tictactoe[1][2] == tictactoe[2][2] == char) or
        # По диагонали
        (tictactoe[0][0] == tictactoe[1][1] == tictactoe[2][2] == char) or
        (tictactoe[0][2] == tictactoe[1][1] == tictactoe[2][0] == char)
    )


def set_user_ans(data):
    row, column = data.split(',')
    row, column = int(row), int(column)

    if tictactoe[row][column] == "-":
        tictactoe[row][column] = "❌"
    else:
        raise Exception


def set_bot_ans():
    while True:
        row, column = random.randint(0, 2), random.randint(0, 2)

        if tictactoe[row][column] == "-":
            tictactoe[row][column] = "⭕"
            break


def is_game_finished():
    return "-" not in tictactoe[0] and "-" not in tictactoe[1] and "-" not in tictactoe[2]


def clear_game_field():
    global tictactoe

    tictactoe = [
        ['-', '-', '-'],
        ['-', '-', '-'],
        ['-', '-', '-']
    ]


def get_game_field():
    keyboard = types.InlineKeyboardMarkup()

    for i in range(0, 3):
        keyboard.add(
            types.InlineKeyboardButton(text=tictactoe[i][0], callback_data="{0},0".format(i)),
            types.InlineKeyboardButton(text=tictactoe[i][1], callback_data="{0},1".format(i)),
            types.InlineKeyboardButton(text=tictactoe[i][2], callback_data="{0},2".format(i)),
        )

    keyboard.add(
        types.InlineKeyboardButton(text='Начать заново', callback_data="restart"),
        types.InlineKeyboardButton(text='Завершить игру', callback_data="finish")
    )

    return keyboard


owm = OWM('e8dbdc96dd5f9b1eabf0666cec75e7c8')
im = Image.open(requests.get('http://openweathermap.org/img/wn/10d@2x.png', stream=True).raw)
weather_manager = owm.weather_manager()
bot = telebot.TeleBot('5906067860:AAGlet1g81-7lALPTvKUFpyRkHeaAFxn4rg')
telebot.State = ""


@bot.message_handler(commands=['start', 'change_mode'])
def start(message):
    keyboard = types.InlineKeyboardMarkup()
    key_tones = types.InlineKeyboardButton(text='Определить тональность текста', callback_data='tones')
    key_weather = types.InlineKeyboardButton(text='Показать погоду в регионе', callback_data='weather')
    key_forecast = types.InlineKeyboardButton(text='Показать прогноз погоды в регионе', callback_data='forecast')
    key_graph = types.InlineKeyboardButton(text='Узнать динамику цены акции', callback_data='stock info')
    key_tictactoe = types.InlineKeyboardButton(text='Играть в крестики-нолики', callback_data='tictactoe')
    keyboard.add(key_tones)
    keyboard.add(key_weather)
    keyboard.add(key_forecast)
    keyboard.add(key_graph)
    keyboard.add(key_tictactoe)
    bot.send_message(message.from_user.id, text='Выбери действие', reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, text='Чтобы выбрать действие пиши /start или /change_mode')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if telebot.State == "tones":
        tone_info = get_text_tone([message.text])
        tone_key = tone_info[0]['predict'][0]
        tone_value = round(tone_info[0]['predict'][1], 2)
        bot.send_message(message.from_user.id, text=f'Тональность: {tone_key}'
                                                    f'\nВероятность: {tone_value}')
    elif telebot.State == "weather":
        weather = get_weather(message.text)
        bot.send_message(message.from_user.id, text=weather['result_str'])
        if 'icon_url' in weather:
            bot.send_photo(message.from_user.id, photo=weather['icon_url'])
    elif telebot.State == 'forecast':
        bot.send_message(message.from_user.id, text='Подожди, данные собираются...')
        forecast = get_forecast(message.text)
        bot.send_message(message.from_user.id, text=forecast)
    elif telebot.State == "stock info":
        ticker = get_ticker(message.text)
        if bool(ticker["work"]):
            bot.send_document(message.from_user.id, InputFile(f'images/{ticker["ticker"]}.png'))
        else:
            bot.send_message(message.from_user.id, text="Простите, но тикер не был найден")
    else:
        bot.send_message(message.from_user.id, text='Я тебя не понимаю, чтобы начать напиши /start')


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == 'tones':
        telebot.State = 'tones'
        bot.send_message(call.message.chat.id, text='Набери текст и я определю его тональность')
    elif call.data == 'weather':
        telebot.State = 'weather'
        bot.send_message(call.message.chat.id, text='Погода в каком городе/регионе тебя интересует?')
    elif call.data == 'forecast':
        telebot.State = 'forecast'
        bot.send_message(call.message.chat.id, text='Прогноз в каком городе/регионе тебя интересует?')
    elif call.data == 'stock info':
        telebot.State = 'stock info'
        bot.send_message(call.message.chat.id, text='Информация о какой акции тебя интересует?')
    elif call.data == 'tictactoe':
        telebot.State = 'tictactoe'
        start_game(call.message.chat.id)
    elif call.data != 'tictactoe' and telebot.State == 'tictactoe':
        ans(call)
    else:
        bot.send_message(call.message.chat.id, text='Неизвестная команда')


bot.polling(none_stop=True, interval=0)