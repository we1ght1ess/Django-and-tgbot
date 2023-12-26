from django.core.management.base import BaseCommand
from django.conf import settings
import telebot
from telebot import TeleBot
from ugc.models import Profile
from ugc.models import Message

class DirectionBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.questions = [
            "",
            "1. Хотите ли вы заниматься программированием?",
            "2. Интересует ли вас работа в суде или адвокатской практике?",
            "3. Предпочитаете ли вы работу с данными и статистикой в социологических исследованиях?",
            "4. Интересует ли вас изучение мировой политики и международной безопасности?",
            "5. Интересует ли вас анализ данных и машинное обучение?",
            "6. Любите ли вы исследовать и анализировать юридические нормы?",
            "7. Хотели бы вы заниматься исследованиями в области социальной динамики?",
            "8. Желаете ли вы заниматься дипломатией и международными переговорами?",
            "9. Предпочитаете ли вы работать над созданием информационных систем для бизнеса?",
            "10. Интересуетесь ли вы вопросами прав человека и социальной юстиции?",
            "11. Интересуетесь ли вы вопросами социокультурного развития и изменения?",
            "12. Любите ли вы анализировать международные экономические процессы?"
        ]
        self.current_question = 0

        self.directions = {
            'Прикладная информатика': "Рекомендуем вам обратить внимание на направление Прикладная информатика!",
            'Юриспруденция': "Рекомендуем вам обратить внимание на направление Юриспруденция!",
            'Социология': "Рекомендуем вам обратить внимание на направление Социология!",
            'Международные отношения': "Рекомендуем вам обратить внимание на направление Международные отношения!"
        }

        self.user_responses = {}

    def restart(self, message):
        self.current_question = 0
        self.user_responses = {}
        self.start(message)

    def start(self, message):
        self.bot.send_message(message.chat.id, "Привет, я бот помогающий выбрать направление в вузе, ответь на пару вопросов и я помогу тебе, хочешь начать?")

    def ask_question(self, message):
        user_response = message.text.lower()
        if user_response == 'да' or user_response == 'нет':
            # Сохраняем ответ пользователя
            self.user_responses[self.current_question] = user_response

            self.current_question += 1

            if self.current_question < len(self.questions):
                self.bot.send_message(message.chat.id, self.questions[self.current_question])
            else:
                self.calculate_direction(message)
        else:
            self.bot.send_message(message.chat.id, "Пожалуйста, ответьте 'Да' или 'Нет'.")

    def calculate_direction(self, message):
    # Подсчет количества ответов "Да" для каждого направления
        directions_count = {direction: 0 for direction in self.directions}

        for question_num, answer in self.user_responses.items():
            if answer == 'да':
                for direction, question_numbers in settings.DIRECTIONS_QUESTIONS.items():
                    if question_num in question_numbers:
                        directions_count[direction] += 1

    # Выбор направления с максимальным количеством ответов "Да"
        max_count = max(directions_count.values())
        global recommended_direction
        recommended_directions = [direction for direction, count in directions_count.items() if count == max_count]

        if len(recommended_directions) == 1:
            recommended_direction = recommended_directions[0]
            response_text = self.directions.get(recommended_direction)
            self.bot.send_message(message.chat.id, response_text)
        else:
            self.bot.send_message(message.chat.id, "Мы не можем подобрать направление для вас.")

        additional_question = "Хотели бы вы получать интересную информацию о поступлении в вуз?"
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.row('Да', 'Нет')
        self.bot.send_message(message.chat.id, additional_question, reply_markup=markup)   

    def handle_additional_question(self, message):
        user_response = message.text.lower()
        if user_response == 'да':
            self.bot.send_message(message.chat.id, "Отлично! Буду стараться радовать тебя информацией.")
            chat_id = message.chat.id
            p, _ = Profile.objects.get_or_create(
                external_id=chat_id,
                defaults={'name': message.from_user.username}
            )
            Message(
                profile =p,
                text = recommended_direction,
                send = user_response,
            ).save()
            self.restart(message)
        elif user_response == 'нет':
            self.bot.send_message(message.chat.id, "Хорошо! Удачного поступления в вуз.")
            chat_id = message.chat.id
            p, _ = Profile.objects.get_or_create(
                external_id=chat_id,
                defaults={'name': message.from_user.username}
            )
            Message(
                profile =p,
                text = recommended_direction,
                send = user_response,
            ).save()
            self.restart(message)
        else:
            self.bot.send_message(message.chat.id, "Пожалуйста, ответьте 'Да' или 'Нет'.")

    def run(self):
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            self.start(message)

        @self.bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            if self.current_question < len(self.questions):
                self.ask_question(message)
            else:
                self.handle_additional_question(message)

        self.bot.polling()

class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **kwargs):
        bot = TeleBot(settings.TOKEN, threaded=False)
        direction_bot = DirectionBot(settings.TOKEN)
        direction_bot.run()