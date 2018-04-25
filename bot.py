import time
import telebot
import database_utilities
import vk
from vk.exceptions import VkAuthError, VkAPIError
from threading import Thread
from datetime import datetime

'Constants and settings'

bot_version = '1.3'
CLIENT_ID = 6004708
V = '5.74'
# TOKEN = '....' # ORIGIGNAL
TOKEN = '....'  # TEST
'''
telebot.apihelper.proxy = {
    'https': 'socks5://52.169.8.120:1080',
    'http': 'socks5://52.169.8.120:1080'
}
'''
bot = telebot.TeleBot(TOKEN)
db = database_utilities.DataBase()
receivers = {}
waiting_password = set()
TERMS = '<b>Внимание   !</b>\n Вводя свои личные данные вы <b>добровольно</b> разрешаете приложению доступ ' \
        'к своим сообщениям. Никакой ответственности, связанной с правовой частью этого ' \
        'соглашения, автор бота на себя не берет.\n' \
        'Пользователю гарантируется, что:\n' \
        '1. Его личные данные(логин, пароль, сообщения, фотографии и т.д.) <b>не хранятся</b>' \
        ' приложением на сервере и <b>не передаются</b> другим лицам\n' \
        '2. Данные, которые хранит приложение для работы: id в телеграмме и ' \
        'токен пользователя с доступом к сообщениям(он не может быть использован ' \
        'со сторонненго ip адреса и действует 24 часа)'

'Vk methods'


class ReceiverThread(Thread):
    MESSAGE_DELAY = 30

    def __init__(self, user_id, token, first_delay):
        self.first_delay = first_delay
        Thread.__init__(self)
        self.id = user_id
        self.killed = False
        self.api = vk.API(vk.Session(access_token=token))

    def parse_username(self, user_id):
        if user_id > 0:
            from_who = self.api.users.get(user_ids=user_id, v=V)[0]
            return from_who[u'first_name'] + ' ' + from_who[u'last_name']
        else:
            from_who = self.api.groups.getById(group_id=-user_id, v=V)[0]
            return from_who[u'name']

    def parse_attachments(self, attachments):
        result = []
        for att in attachments:
            t = att['type']
            if t == 'photo':
                photo = att[t]
                if 'photo_2560' in photo:
                    photo_link = photo['photo_2560']
                elif 'photo_1280' in photo:
                    photo_link = photo['photo_1280']
                elif 'photo_807' in photo:
                    photo_link = photo['photo_807']
                elif 'photo_604' in photo:
                    photo_link = photo['photo_604']
                elif 'photo_130' in photo:
                    photo_link = photo['photo_130']
                else:
                    photo_link = photo['photo_75']
                photo_link = "'" + photo_link + "'"
                result += ['bot.send_photo(self.id,' + photo_link + ')']
            elif t == 'video':
                video_link = att['video']['player']
                video_link = "'" + video_link + "'"
                result += ['bot.send_video(self.id,' + video_link + ')']
            elif t == 'audio':
                audio_link = att['audio']['url']
                audio_link = "'" + audio_link + "'"
                result += ['bot.send_audio(self.id,' + audio_link + ')']
            elif t == 'doc':
                doc_link = att['doc']['url']
                doc_link = "'" + doc_link + "'"
                result += ['bot.send_document(self.id,' + doc_link + ')']
            elif t == 'link':
                url = att['link']['url']
                url = "'" + url + "'"
                result += ['bot.send_message(self.id,' + url + ')']
            elif t == 'market_album':
                result += ["bot.send_message(self.id, 'Прикеплена подборка товаров' )"]
            elif t == 'wall':
                post = att['wall']
                text = 'Пост <b>' + self.parse_username(post['from_id']) + '</b> на стене <b>' \
                       + self.parse_username(post['to_id']) + '</b>:\n'
                timestamp = datetime.fromtimestamp(post['date'])
                text += '[' + str(timestamp) + ']:\n'
                text += post['text']
                to_send = []
                bot.send_message(self.id, text, parse_mode='HTML')
                if 'attachments' in post:
                    to_send += self.parse_attachments(post['attachments'])
                for action in to_send:
                    eval(action)
            elif t == 'wall_reply':
                pass
            elif t == 'sticker':
                sticker_images = att['sticker']['images']
                best_link = sticker_images[len(sticker_images) - 1]['url']
                best_link = "'" + best_link + "'"
                result += ['bot.send_photo(self.id,' + best_link + ')']
            elif t == 'gift':
                result += ["bot.send_message(self.id, 'Прикреплен подарок')"]
        return result

    def parse_message(self, mes):
        text = ''
        text += ('<i>' + mes[u'title'] + '</i>\n') if ('title' in mes and bool(mes['title'])) else ''
        timestamp = datetime.fromtimestamp(mes[u'date'])
        text += '<b>' + self.parse_username(mes['user_id']) + '</b>'
        text += '\n' + '[' + str(timestamp) + ']' + ':\n'
        time.sleep(0.25)

        text += mes[u'body']
        if 'action' in mes:
            if mes['action'] == 'chat_invite_user':
                text += 'Пригласил пользователя ' + self.parse_username(mes['action_mid'])
            elif mes['action'] == 'chat_photo_update':
                text += 'Обновил фотографию беседы'
            elif mes['action'] == 'chat_photo_remove':
                text += 'Удалил фотографию беседы'
            elif mes['action'] == 'chat_create':
                text += 'Создал беседу'
            elif mes['action'] == 'chat_title_update':
                text += 'Сменил название беседы на: \n<i>' + mes['action_text'] + '</i>'
            elif mes['action'] == 'chat_kick_user':
                text += 'Исключил пользователя: ' + self.parse_username(mes['action_mid'])
            elif mes['action'] == 'chat_pin_message':
                text += 'Закрепил сообщение: \n<i>' + mes['action_text'] + '</i>'
            elif mes['action'] == 'chat_unpin_message':
                text += 'Открепил сообщение'
            else:
                text += 'Присоеденися к беседе'
        to_send = []
        bot.send_message(self.id, text, parse_mode='HTML')
        if 'attachments' in mes:
            to_send += self.parse_attachments(mes[u'attachments'])
        for action in to_send:
            eval(action)
        if 'fwd_messages' in mes:
            bot.send_message(self.id, '<i>Ветка пересланных сообщений начинается:</i>', parse_mode='HTML')
            fwd_messages = mes[u'fwd_messages']
            for message in fwd_messages:
                self.parse_message(message)
            time.sleep(0.4)
            bot.send_message(self.id, '<i>Ветка пересланных сообщений кончается</i>', parse_mode='HTML')

    def run(self):
        while not self.killed:
            delta = time.time()
            try:
                last_messages = self.api.messages.get(time_offset=self.MESSAGE_DELAY + self.first_delay, v=V)[u'items']
                self.first_delay = 0
                # TODO answering by reply
                for mes in reversed(last_messages):
                    self.parse_message(mes)
            except VkAPIError as error:
                print(error)
                if error.code == 5:
                    bot.send_message(self.id, 'Ошибка в аутентификации, пройдите ее еще раз')
                    auth(self.id)
            except Exception as error:
                print(error)
            finally:
                delta = time.time() - delta
                if self.MESSAGE_DELAY - delta > 0:
                    time.sleep(self.MESSAGE_DELAY - delta)

    def kill(self):
        self.killed = True


def check_token(user_info):
    try:
        test = vk.API(vk.Session(user_info[1]))
        test.users.get(users_id=1, v=V)
        return True
    except (VkAuthError, VkAPIError) as error:
        print(error)
        return False


def start_thread(user_info, first_delay=0):
    bot.send_message(user_info[0], 'Процесс получения ваших сообщений начат')
    if check_token(user_info):
        receivers[user_info[0]] = ReceiverThread(user_info[0], user_info[1], first_delay)
        receivers[user_info[0]].start()
    else:
        bot.send_message(user_info[0], 'Токен(логин, пароль) не верный, трай хардер')
        auth(user_info[0])


def stop_thread(user_id):
    if user_id in receivers:
        receivers[user_id].kill()
        del receivers[user_id]


'Telegram bot main'


def auth(user_id):
    stop_thread(user_id)
    bot.send_message(user_id, TERMS, parse_mode='HTML')
    bot.send_message(user_id, 'Введите логин и пароль разделяя их пробелом')
    waiting_password.add(user_id)


@bot.message_handler(commands=['help'])
def send_help(message):
    mes = '''Этот бот позволяет получать через него сообщения которые вам приходят вк.
    Список команд:
    /start - включить получение сообщений(если не зарегистрированы, то зарегистрирует вас)
    /stop - прекратить получение
    /reauth - перезарегистрироваться
    /delete - удалить свой токен из базы
    /about - ну понятно...
    /terms - условия использования
    /help - список команд и инфо
    '''
    bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=['start'])
def init(message):
    if message.chat.id in receivers:
        bot.send_message(message.chat.id, 'Вы уже получаете сообщения')
    else:
        if message.chat.id not in db:
            auth(message.chat.id)
        else:
            user_info = db.get_info(message.chat.id)
            start_thread(user_info)


@bot.message_handler(commands=['reauth'])
def re_auth(message):
    auth(message.chat.id)


@bot.message_handler(commands=['stop'])
def stop(message):
    if message.chat.id in receivers:
        stop_thread(message.chat.id)
        bot.send_message(message.chat.id, 'Получение сообщений остановлено, пришли /delete '
                                          'чтобы удалить свой токен из базы')
    elif message.chat.id in waiting_password:
        waiting_password.remove(message.chat.id)
        bot.send_message(message.chat.id, 'Окей, пиши /start или /reauth чтобы войти')
    else:
        bot.send_message(message.chat.id, 'Процесс и так остановлен')


@bot.message_handler(func=lambda m: m.chat.id in waiting_password)
def apply_pass(message):
    try:
        login, password = message.text.split()
        this_user_token = vk.AuthSession(app_id=CLIENT_ID, user_login=login,
                                         user_password=password, scope='messages').access_token
        waiting_password.remove(message.chat.id)
        user_info = [message.chat.id, this_user_token, int(time.time()), 86400]
        if message.chat.id in db:
            info = db.get_info(message.chat.id)
            start_thread(user_info, first_delay=info[2] + info[3])
            db.remove(message.chat.id)
        else:
            start_thread(user_info)
        db.add(user_info)
    except (VkAuthError, ValueError):
        bot.send_message(message.chat.id, 'Неверный логин/пароль, давай еще раз')


@bot.message_handler(commands=['delete'])
def delete_user(message):
    if message.chat.id in receivers:
        bot.send_message(message.chat.id, 'Удалить токен невозможно, идет процесс получения сообщений')
    else:
        db.remove(message.chat.id)
        bot.send_message(message.chat.id, 'Вы успешно удалены')


@bot.message_handler(commands=['about'])
def send_about(message):
    text = '''Автор бота, по всем вопросам - @hazzus
    Bot version {version}
    '''.format(version=bot_version)
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['terms'])
def send_terms(message):
    bot.send_message(message.chat.id, TERMS, parse_mode='HTML')


if __name__ == '__main__':
    # bot.infinity_polling(True)
    while True:
        try:
            bot.polling(none_stop=True)
        except KeyboardInterrupt:
            print('Process terminated by user')
            quit(0)
        except Exception as e:
            print(e)
