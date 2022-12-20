import telebot
from telebot import types
from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel
from pyowm import OWM
from PIL import Image
from translate import Translator
import config
import requests


owm = OWM(config.open_weather_token)

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
    result.append({ 'text': sentences[i], 'tone': tone, 'predict': predict })
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

im = Image.open(requests.get('http://openweathermap.org/img/wn/10d@2x.png', stream=True).raw)
weather_manager = owm.weather_manager()
bot = telebot.TeleBot(config.telegram_token)
telebot.State = ""

@bot.message_handler(commands=['start', 'change_mode'])
def start(message):
  keyboard = types.InlineKeyboardMarkup()
  key_tones = types.InlineKeyboardButton(text='Определить тональность текста', callback_data='tones')
  key_other = types.InlineKeyboardButton(text='Показать погоду в регионе', callback_data='weather')
  keyboard.add(key_tones)
  keyboard.add(key_other)
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
  else:
    bot.send_message(message.from_user.id, text='Я тебя не понимаю, чтобы начать напиши /start')

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
  telebot.State = call.data
  if call.data == 'tones':
    bot.send_message(call.message.chat.id, text='Набери текст и я определю его тональность')
  elif call.data == 'weather':
    bot.send_message(call.message.chat.id, text='Погода в каком городе/регионе тебя интересует?')
  else:
    bot.send_message(call.message.chat.id, text='Неизвестная команда')

bot.polling(none_stop=True, interval=0)