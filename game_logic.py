import random
from typing import List, Dict, Any, Tuple

class LoveNumberPuzzle:
    def __init__(self):
        self.levels = self.generate_levels(30)
        self.MAX_LEVEL = len(self.levels)
        
        self.love_messages = [
            "Ти - моє сонечко, що освітлює кожен мій день 🌞",
            "Кохання до тебе з кожним днем стає сильнішим 💖",
            "Твої очі - це зірки, що вказують мені шлях ✨",
            "Кожен мій вдих наповнений твоїм ім'ям 💋",
            "Ти - мелодія мого серця 🎵",
            "Навіть у найтемніші ночі ти світишся для мене ⭐",
            "Твоє кохання - це моя суперсила 💪",
            "Разом ми - непереможна команда! 💑",
            "Ти робиш мій світ яскравішим 🌈",
            "Кожна хвилина з тобою - цінність 💎",
            "Твої посмішки лікують мою душу 😊",
            "Ти - моя вічна весна 🌸",
            "Твої думки - це мої найкращі мрії 💭",
            "Ти змушуєш мене вірити в чарівність ❤️‍🔥",
            "Навіть відстань між нами не може зламати наше кохання 🌍",
            "Ти - моя історія любові 📖",
            "Твоє серце б'ється в моїй душі 💓",
            "Ти - моя музика душі 🎼",
            "Твої обійми - це мій дім 🏠",
            "Ти робиш мене кращим щодня 🌟",
            "Твоє кохання - це моя відповідь на життя 💝",
            "Ти - моя натхненна муза 🎨",
            "Твої слова - це поезія для моєї душі 📝",
            "Ти - моя вічна любов 💞",
            "Твої думки про мене зігрівають серце 🔥",
            "Ти - моя радість кожного дня ☀️",
            "Твоє кохання - це моя відповідь на всі запитання ❓",
            "Ти - моя вічна весна в серці 🌷",
            "Твої обійми - це мій безпечний світ 🛡️",
            "Ти - відповідь на всі мої молитви 🙏"
        ]
        
        self.GRID_W = 5
        self.GRID_H = 8
        self.bonus_costs = {'destroy': 5, 'shuffle': 10, 'explosion': 20}

    def generate_levels(self, count: int) -> List[Dict]:
        levels = []
        target = 64
        base_numbers = [2, 4, 8]
        
        for i in range(count):
            level = {
                'numbers': base_numbers.copy(),
                'target': target,
                'new_numbers': self.generate_new_numbers(target),
                'max': base_numbers[-1],
                'xp_to_next': 10 + i * 2
            }
            
            levels.append(level)
            target *= 2
            
            if i % 3 == 2 and len(base_numbers) < 5:
                base_numbers.append(base_numbers[-1] * 2)
                
            if i >= 15 and len(base_numbers) < 6:
                base_numbers.append(base_numbers[-1] * 2)
                
        return levels

    def generate_new_numbers(self, target: int) -> List[int]:
        new_numbers = []
        num = target // 8
        for i in range(8):
            if num <= target:
                new_numbers.append(num)
                num *= 2
        return new_numbers

    def initialize_game(self, level_num: int = 0) -> Dict[str, Any]:
        level = self.levels[level_num]
        grid = []
        
        for x in range(self.GRID_W):
            grid.append([])
            for y in range(self.GRID_H):
                grid[x].append({
                    'number': random.choice(level['numbers']),
                    'merged': False
                })
        
        return {
            'current_level': level_num,
            'grid': grid,
            'selected': [],
            'xp': 0,
            'xp_to_next': level['xp_to_next'],
            'max_number': level['max'],
            'message_count': 0,
            'active_bonus': None,
            'game_state': 'playing'
        }

    def format_number(self, num: int) -> str:
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B".replace('.0', '')
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M".replace('.0', '')
        if num >= 10_000:
            return f"{num/1_000:.0f}K"
        if num >= 1_000:
            return f"{num/1_000:.1f}K".replace('.0', '')
        return str(num)

    def is_adjacent(self, a: Dict, b: Dict) -> bool:
        return abs(a['x'] - b['x']) <= 1 and abs(a['y'] - b['y']) <= 1

    def get_random_initial_number(self, level_num: int) -> int:
        level = self.levels[level_num]
        return random.choice(level['numbers'])

    def is_valid_result_number(self, num: int, level_num: int) -> bool:
        level = self.levels[level_num]
        return num in level['numbers'] or num in level['new_numbers']

    def calculate_xp(self, chain_length: int) -> int:
        xp_map = {2: 1, 3: 4, 4: 8, 5: 15}
        return xp_map.get(chain_length, 25)

    def get_random_love_message(self, chain_length: int) -> str:
        if chain_length >= 6:
            return "Вау! Ти геній кохання! 💖 Наша любов така ж сильна!"
        elif chain_length >= 4:
            return "Чудово! Наша любов росте як твої навички! 🌟"
        else:
            return random.choice(self.love_messages)

    def process_move(self, game_data: Dict, selected_cells: List[Dict]) -> Dict[str, Any]:
        if len(selected_cells) < 2:
            return {
                'success': False,
                'message': "Оберіть хоча б 2 клітинки! 💕"
            }

        # Проверяем цепочку
        chain_numbers = []
        for cell in selected_cells:
            chain_numbers.append(game_data['grid'][cell['x']][cell['y']]['number'])

        new_value = sum(chain_numbers)
        
        if not self.is_valid_result_number(new_value, game_data['current_level']):
            return {
                'success': False,
                'message': "Спробуй іншу комбінацію, кохана! 💕"
            }

        # Обновляем сетку
        last_cell = selected_cells[-1]
        game_data['grid'][last_cell['x']][last_cell['y']]['number'] = new_value
        
        for i in range(len(selected_cells) - 1):
            cell = selected_cells[i]
            game_data['grid'][cell['x']][cell['y']]['number'] = self.get_random_initial_number(game_data['current_level'])

        # Начисляем XP
        xp_earned = self.calculate_xp(len(selected_cells))
        game_data['xp'] += xp_earned
        game_data['message_count'] += 1

        # Проверяем победу
        level = self.levels[game_data['current_level']]
        won = any(
            game_data['grid'][x][y]['number'] == level['target']
            for x in range(self.GRID_W)
            for y in range(self.GRID_H)
        )

        return {
            'success': True,
            'xp_earned': xp_earned,
            'message': self.get_random_love_message(len(selected_cells)),
            'won': won,
            'new_value': new_value
        }

    def use_bonus(self, game_data: Dict, bonus_type: str, x: int = None, y: int = None) -> Dict[str, Any]:
        cost = self.bonus_costs[bonus_type]
        
        if game_data['xp'] < cost:
            return {
                'success': False,
                'message': "Недостатньо очків кохання! ❤️‍🔥"
            }

        game_data['xp'] -= cost
        
        if bonus_type == 'shuffle':
            self.shuffle_grid(game_data)
            return {
                'success': True,
                'message': "Поле перемішано з любов'ю! 💫"
            }
        elif bonus_type == 'destroy' and x is not None and y is not None:
            game_data['grid'][x][y]['number'] = self.get_random_initial_number(game_data['current_level'])
            return {
                'success': True,
                'message': "Клітинку розбито з любов'ю! 💖"
            }
        elif bonus_type == 'explosion' and x is not None and y is not None:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.GRID_W and 0 <= ny < self.GRID_H:
                        game_data['grid'][nx][ny]['number'] = self.get_random_initial_number(game_data['current_level'])
            return {
                'success': True,
                'message': "Вибух кохання! 💥❤️"
            }
        
        return {'success': False, 'message': "Невідомий бонус"}

    def shuffle_grid(self, game_data: Dict):
        all_numbers = []
        for x in range(self.GRID_W):
            for y in range(self.GRID_H):
                all_numbers.append(game_data['grid'][x][y]['number'])
        
        random.shuffle(all_numbers)
        
        index = 0
        for x in range(self.GRID_W):
            for y in range(self.GRID_H):
                game_data['grid'][x][y]['number'] = all_numbers[index]
                index += 1

    def can_advance_level(self, game_data: Dict) -> bool:
        return game_data['xp'] >= game_data['xp_to_next']

    def advance_level(self, game_data: Dict) -> Dict[str, Any]:
        if game_data['current_level'] < self.MAX_LEVEL - 1:
            if self.can_advance_level(game_data):
                new_level = game_data['current_level'] + 1
                level_data = self.initialize_game(new_level)
                level_data['current_level'] = new_level
                level_data['message_count'] = game_data['message_count']
                return {
                    'success': True,
                    'new_level': new_level,
                    'game_data': level_data,
                    'message': f"Рівень {new_level + 1}! Нові виклики! 🌟"
                }
            else:
                return {
                    'success': False,
                    'message': f"Потрібно {game_data['xp_to_next']} очків кохання! ❤️"
                }
        else:
            return {
                'success': True,
                'won_game': True,
                'message': "Вітаю! Ти пройшла всі рівні! Ти найкраща! 💝"
            }
