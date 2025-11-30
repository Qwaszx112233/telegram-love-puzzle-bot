"""
Мінімальний бот для Love Number Puzzle
Не вимагає встановлення додаткових бібліотек
"""

import json
import time
import urllib.request
import urllib.parse
import sys
from config import BOT_TOKEN, WEB_APP_URL
from database import Database
from game_logic import LoveNumberPuzzle

# Глобальные объекты
db = Database()
game = LoveNumberPuzzle()

def send_message(chat_id, text, keyboard=None):
    """Надсилання повідомлення через Telegram Bot API"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if keyboard:
        data['reply_markup'] = json.dumps(keyboard)
    
    try:
        data_encoded = urllib.parse.urlencode(data).encode()
        with urllib.request.urlopen(url, data_encoded) as response:
            result = json.loads(response.read().decode())
            return result.get('ok', False)
    except Exception as e:
        print(f"Помилка надсилання повідомлення: {e}")
        return False

def send_callback_answer(callback_query_id, text, show_alert=False):
    """Надсилання відповіді на callback запит"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery'
    
    data = {
        'callback_query_id': callback_query_id,
        'text': text,
        'show_alert': show_alert
    }
    
    try:
        data_encoded = urllib.parse.urlencode(data).encode()
        with urllib.request.urlopen(url, data_encoded) as response:
            result = json.loads(response.read().decode())
            return result.get('ok', False)
    except Exception as e:
        print(f"Помилка надсилання відповіді на callback: {e}")
        return False

def edit_message_text(chat_id, message_id, text, keyboard=None):
    """Редагування повідомлення"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText'
    
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if keyboard:
        data['reply_markup'] = json.dumps(keyboard)
    
    try:
        data_encoded = urllib.parse.urlencode(data).encode()
        with urllib.request.urlopen(url, data_encoded) as response:
            result = json.loads(response.read().decode())
            return result.get('ok', False)
    except Exception as e:
        print(f"Помилка редагування повідомлення: {e}")
        return False

def get_updates(offset=None):
    """Отримання оновлень від Telegram"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
    params = {'timeout': 30}
    
    if offset:
        params['offset'] = offset
    
    try:
        url_with_params = f"{url}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url_with_params) as response:
            data = json.loads(response.read().decode())
            return data.get('result', [])
    except Exception as e:
        print(f"Помилка отримання оновлень: {e}")
        return []

def create_game_keyboard(game_data, user_id):
    """Створення клавіатури для гри"""
    keyboard = []
    
    # Створюємо сітку 5x8
    for y in range(game.GRID_H):
        row = []
        for x in range(game.GRID_W):
            cell = game_data['grid'][x][y]
            number = cell['number']
            display_text = game.format_number(number)
            
            # Перевіряємо, чи клітинка вибрана
            is_selected = any(s['x'] == x and s['y'] == y for s in game_data.get('selected', []))
            if is_selected:
                display_text = f"✅{display_text}"
            
            callback_data = f"cell_{user_id}_{x}_{y}"
            row.append({'text': display_text, 'callback_data': callback_data})
        keyboard.append(row)
    
    # Додаємо інформацію про поточну суму
    if game_data.get('selected', []):
        current_sum = sum(game_data['grid'][s['x']][s['y']]['number'] for s in game_data['selected'])
        keyboard.append([{'text': f"🔢 Сума: {game.format_number(current_sum)}", 'callback_data': 'info_sum'}])
    
    # Бонуси
    bonus_row = [
        {'text': f"💖 Розбити ({game.bonus_costs['destroy']})", 'callback_data': f"bonus_destroy_{user_id}"},
        {'text': f"🔄 Перемішати ({game.bonus_costs['shuffle']})", 'callback_data': f"bonus_shuffle_{user_id}"},
        {'text': f"💥 Вибух ({game.bonus_costs['explosion']})", 'callback_data': f"bonus_explosion_{user_id}"}
    ]
    keyboard.append(bonus_row)
    
    # Кнопки управління
    control_row = [
        {'text': "↩️ Скасувати", 'callback_data': f"undo_{user_id}"},
        {'text': "🔄 Скинути", 'callback_data': f"reset_{user_id}"},
        {'text': "⭐ Далі", 'callback_data': f"next_level_{user_id}"},
        {'text': "🏠 Меню", 'callback_data': f"menu_{user_id}"}
    ]
    keyboard.append(control_row)
    
    return {'inline_keyboard': keyboard}

def start_game(user_id, chat_id, user_name):
    """Початок гри для користувача"""
    # Отримуємо прогрес користувача
    user_progress = db.get_user_progress(user_id)
    
    # Ініціалізуємо гру
    if not user_progress['game_state'].get('grid'):
        game_data = game.initialize_game(user_progress['current_level'])
        user_progress['game_state'] = game_data
        db.update_user_progress(user_id, user_progress)
    else:
        game_data = user_progress['game_state']
    
    # Створюємо клавіатуру гри
    keyboard = create_game_keyboard(game_data, user_id)
    
    # Текст з інформацією про гру
    game_text = f"""
🎮 <b>Love Number Puzzle</b> 💖

👤 Гравець: {user_name}
📊 Рівень: {game_data['current_level'] + 1}
⭐ Досвід: {game_data['xp']}/{game_data['xp_to_next']}
💝 Повідомлень: {game_data['message_count']}

🎯 Об'єднуй числа, щоб отримати {game.format_number(game.levels[game_data['current_level']]['target'])}!

Обирай клітинки для створення ланцюжка! 💕
    """
    
    return send_message(chat_id, game_text, keyboard)

def handle_callback_query(update):
    """Обробка callback запитів"""
    callback_query = update['callback_query']
    callback_query_id = callback_query['id']
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    data = callback_query['data']
    user_id = callback_query['from']['id']
    user_name = callback_query['from'].get('first_name', 'друг')
    
    print(f"Callback від {user_name} ({user_id}): {data}")
    
    try:
        if data.startswith('cell_'):
            # Обробка вибору клітинки
            parts = data.split('_')
            if len(parts) >= 4:
                target_user_id = int(parts[1])
                x, y = int(parts[2]), int(parts[3])
                
                if target_user_id != user_id:
                    send_callback_answer(callback_query_id, "Це не ваша гра! 🙅‍♂️", True)
                    return
                
                # Отримуємо прогрес користувача
                user_progress = db.get_user_progress(user_id)
                game_data = user_progress['game_state']
                
                # Додаємо клітинку до вибраних
                selected = game_data.get('selected', [])
                
                # Перевіряємо, чи клітинка вже вибрана
                existing_index = None
                for i, cell in enumerate(selected):
                    if cell['x'] == x and cell['y'] == y:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    # Якщо клітинка вже вибрана, видаляємо її (відміна вибору)
                    selected = selected[:existing_index + 1]  # Залишаємо тільки до цієї клітинки
                else:
                    # Додаємо нову клітинку
                    selected.append({'x': x, 'y': y})
                
                game_data['selected'] = selected
                user_progress['game_state'] = game_data
                db.update_user_progress(user_id, user_progress)
                
                # Оновлюємо повідомлення
                keyboard = create_game_keyboard(game_data, user_id)
                game_text = f"""
🎮 <b>Love Number Puzzle</b> 💖

👤 Гравець: {user_name}
📊 Рівень: {game_data['current_level'] + 1}
⭐ Досвід: {game_data['xp']}/{game_data['xp_to_next']}
💝 Повідомлень: {game_data['message_count']}

🎯 Об'єднуй числа, щоб отримати {game.format_number(game.levels[game_data['current_level']]['target'])}!

Обирай клітинки для створення ланцюжка! 💕
                """
                
                edit_message_text(chat_id, message_id, game_text, keyboard)
                send_callback_answer(callback_query_id, f"Вибрано клітинку {x},{y}")
        
        elif data.startswith('undo_'):
            # Скасування останнього ходу
            parts = data.split('_')
            if len(parts) >= 2:
                target_user_id = int(parts[1])
                
                if target_user_id != user_id:
                    send_callback_answer(callback_query_id, "Це не ваша гра! 🙅‍♂️", True)
                    return
                
                # Отримуємо прогрес користувача
                user_progress = db.get_user_progress(user_id)
                game_data = user_progress['game_state']
                
                # Видаляємо останню вибрану клітинку
                selected = game_data.get('selected', [])
                if selected:
                    selected.pop()
                    game_data['selected'] = selected
                    user_progress['game_state'] = game_data
                    db.update_user_progress(user_id, user_progress)
                    
                    # Оновлюємо повідомлення
                    keyboard = create_game_keyboard(game_data, user_id)
                    game_text = f"""
🎮 <b>Love Number Puzzle</b> 💖

👤 Гравець: {user_name}
📊 Рівень: {game_data['current_level'] + 1}
⭐ Досвід: {game_data['xp']}/{game_data['xp_to_next']}
💝 Повідомлень: {game_data['message_count']}

🎯 Об'єднуй числа, щоб отримати {game.format_number(game.levels[game_data['current_level']]['target'])}!

Обирай клітинки для створення ланцюжка! 💕
                    """
                    
                    edit_message_text(chat_id, message_id, game_text, keyboard)
                    send_callback_answer(callback_query_id, "Останній хід скасовано ↩️")
                else:
                    send_callback_answer(callback_query_id, "Немає ходів для скасування")
        
        elif data.startswith('reset_'):
            # Скидання вибору
            parts = data.split('_')
            if len(parts) >= 2:
                target_user_id = int(parts[1])
                
                if target_user_id != user_id:
                    send_callback_answer(callback_query_id, "Це не ваша гра! 🙅‍♂️", True)
                    return
                
                # Отримуємо прогрес користувача
                user_progress = db.get_user_progress(user_id)
                game_data = user_progress['game_state']
                
                # Очищуємо вибір
                game_data['selected'] = []
                user_progress['game_state'] = game_data
                db.update_user_progress(user_id, user_progress)
                
                # Оновлюємо повідомлення
                keyboard = create_game_keyboard(game_data, user_id)
                game_text = f"""
🎮 <b>Love Number Puzzle</b> 💖

👤 Гравець: {user_name}
📊 Рівень: {game_data['current_level'] + 1}
⭐ Досвід: {game_data['xp']}/{game_data['xp_to_next']}
💝 Повідомлень: {game_data['message_count']}

🎯 Об'єднуй числа, щоб отримати {game.format_number(game.levels[game_data['current_level']]['target'])}!

Обирай клітинки для створення ланцюжка! 💕
                """
                
                edit_message_text(chat_id, message_id, game_text, keyboard)
                send_callback_answer(callback_query_id, "Вибір скинуто 🔄")
        
        elif data.startswith('menu_'):
            # Повернення до меню
            parts = data.split('_')
            if len(parts) >= 2:
                target_user_id = int(parts[1])
                
                if target_user_id != user_id:
                    send_callback_answer(callback_query_id, "Це не ваша гра! 🙅‍♂️", True)
                    return
            
            # Показуємо головне меню
            keyboard = {
                'inline_keyboard': [[
                    {
                        'text': '🎮 Грати в Love Puzzle',
                        'web_app': {'url': WEB_APP_URL}
                    }
                ]]
            }
            
            menu_text = f"""
💖 <b>Love Number Puzzle</b> 💖

Привіт {user_name}! Ласкаво просимо до гри любові та чисел! ❤️

🎮 <b>Особливості гри:</b>
• 30 романтичних рівнів
• Система збереження прогресу
• Любовні фрази та послання
• Красиві анімації серця
• Автоматичне збереження

Натисніть кнопку нижче, щоб розпочати гру! 💕
            """
            
            send_message(chat_id, menu_text, keyboard)
            send_callback_answer(callback_query_id, "Повернення до меню 🏠")
        
        elif data == 'info_sum':
            send_callback_answer(callback_query_id, "Поточна сума ланцюжка")
            
        else:
            send_callback_answer(callback_query_id, "Дія виконана")
            
    except Exception as e:
        print(f"Помилка обробки callback: {e}")
        send_callback_answer(callback_query_id, "Помилка обробки запиту 😞", True)

def main():
    """Головна функція бота"""
    print("=" * 60)
    print("💖 Love Number Puzzle Bot 💖")
    print("=" * 60)
    print("Бот запущений! Для зупинки натисніть Ctrl+C")
    print(f"Web App: {WEB_APP_URL}")
    print("=" * 60)

    last_update_id = 0

    while True:
        try:
            updates = get_updates(last_update_id + 1)

            for update in updates:
                last_update_id = update['update_id']

                if 'message' in update:
                    message = update['message']
                    chat_id = message['chat']['id']
                    text = message.get('text', '')
                    user_id = message['from']['id']
                    user_name = message['from'].get('first_name', 'друг')

                    print(f"Повідомлення від {user_name}: {text}")

                    if text == '/start':
                        keyboard = {
                            'inline_keyboard': [[
                                {
                                    'text': '🎮 Грати в Love Puzzle',
                                    'web_app': {'url': WEB_APP_URL}
                                }
                            ]]
                        }

                        welcome_text = f"""
💖 <b>Love Number Puzzle</b> 💖

Привіт {user_name}! Ласкаво просимо до гри любові та чисел! ❤️

🎮 <b>Особливості гри:</b>
• 30 романтичних рівнів
• Система збереження прогресу
• Любовні фрази та послання
• Красиві анімації серця
• Автоматичне збереження

🎯 <b>Як грати:</b>
Об'єднуй однакові числа або числа, що відрізняються в 2 рази!
Кожне поєднання відкриває нову любовну фразу.

Натисніть кнопку нижче, щоб розпочати гру! 💕
                        """
                        if send_message(chat_id, welcome_text, keyboard):
                            print(f"Привітання надіслано користувачу {user_name}")
                    elif text == '/game':
                        # Запуск гри через бота
                        if start_game(user_id, chat_id, user_name):
                            print(f"Гра запущена для користувача {user_name}")

                    elif text == '/help':
                        help_text = """
<b>Доступні команди:</b>
/start - Почати роботу з ботом
/game - Запустити гру
/help - Показати цю довідку
/about - Про гру та автора
/support - Допомога та підтримка

<b>Особливості гри:</b>
💾 Автозбереження прогресу
💝 Любовні фрази при кожному ході
🎯 30 рівнів складності
🌟 Бонуси та покращення

Натисніть кнопку нижче, щоб почати грати! 🎮
                        """
                        keyboard = {
                            'inline_keyboard': [[
                                {
                                    'text': '🎮 Грати в Love Puzzle',
                                    'web_app': {'url': WEB_APP_URL}
                                }
                            ]]
                        }
                        if send_message(chat_id, help_text, keyboard):
                            print(f"Довідка надіслана користувачу {user_name}")

                    elif text == '/about':
                        about_text = """
<b>💖 Love Number Puzzle 💖</b>

🎮 Романтична гра-головоломка з числами
✨ Створено з любов'ю для найкращої дружини

🌟 <b>Особливості:</b>
• 30 унікальних рівнів
• 40+ любовних фраз
• Система збереження
• Красиві анімації

❤️ Кожна гра - це нове визнання в коханні!

<code>Версія: 2.0</code>
                        """
                        keyboard = {
                            'inline_keyboard': [[
                                {
                                    'text': '🎮 Грати зараз',
                                    'web_app': {'url': WEB_APP_URL}
                                }
                            ]]
                        }
                        if send_message(chat_id, about_text, keyboard):
                            print(f"Інформація про гру надіслана користувачу {user_name}")

                    elif text == '/support':
                        support_text = """
<b>🆘 Допомога та підтримка</b>

Якщо виникли питання або проблеми з грою:

📧 Зв'яжіться з розробником:
@bergmann1

🔧 <b>Поширені проблеми:</b>
• Гра не завантажується - перевірте інтернет
• Не зберігається прогрес - дозвольте cookies
• Помилки - перезапустіть гру

💡 <b>Поради:</b>
• Використовуйте останню версію Telegram
• Переконайтесь, що стабільне інтернет-з'єднання

Дякуємо за гру! 💕
                        """
                        if send_message(chat_id, support_text):
                            print(f"Підтримка надіслана користувачу {user_name}")

                    else:
                        help_text = f"""
Привіт {user_name}! 👋

Я бот для гри <b>Love Number Puzzle</b> - романтичної головоломки з числами та любовними фразами! 💖

<b>Використовуй команди:</b>
/start - Почати роботу
/game - Запустити гру
/help - Отримати довідку
/about - Про гру
/support - Допомога

Або просто натисніть кнопку нижче, щоб почати грати! 🎮
                        """
                        keyboard = {
                            'inline_keyboard': [[
                                {
                                    'text': '🎮 Грати в Love Puzzle',
                                    'web_app': {'url': WEB_APP_URL}
                                }
                            ]]
                        }
                        if send_message(chat_id, help_text, keyboard):
                            print(f"Відповідь надіслана користувачу {user_name}")
                
                elif 'callback_query' in update:
                    handle_callback_query(update)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n" + "=" * 50)
            print("Бот зупинений користувачем.")
            print("=" * 50)
            break
        except Exception as e:
            print(f"Помилка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    # Перевірка токена
    if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ ПОМИЛКА: Встановіть правильний BOT_TOKEN у файлі!")
        sys.exit(1)
    
    # Перевірка з'єднання
    print("Перевірка з'єднання з Telegram API...")
    try:
        updates = get_updates()
        print("✅ З'єднання з Telegram API встановлено!")
    except Exception as e:
        print(f"❌ Помилка з'єднання з Telegram API: {e}")
        print("Перевірте інтернет з'єднання та правильність BOT_TOKEN")
        sys.exit(1)
    
    main()