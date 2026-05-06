"""
В данном модуле написана подпрограмма первичной настройки FunPayCardinal'а.
"""

import os
from configparser import ConfigParser
import time
import telebot
from colorama import Fore, Style
from Utils.cardinal_tools import validate_proxy, hash_password, build_proxy, check_proxy
from Utils.config_loader import load_main_config

# locale#locale#locale
default_config = {
    "FunPay": {
        "golden_key": "",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "autoRaise": "0",
        "autoResponse": "0",
        "autoDelivery": "0",
        "multiDelivery": "0",
        "autoRestore": "0",
        "autoDisable": "0",
        "oldMsgGetMode": "0",
        "locale": "ru"
    },
    "Telegram": {
        "enabled": "0",
        "token": "",
        "secretKeyHash": "ХешСекретногоПароля",
        "blockLogin": "0",
        "proxy": ""
    },

    "BlockList": {
        "blockDelivery": "0",
        "blockResponse": "0",
        "blockNewMessageNotification": "0",
        "blockNewOrderNotification": "0",
        "blockCommandNotification": "0"
    },

    "NewMessageView": {
        "includeMyMessages": "1",
        "includeFPMessages": "1",
        "includeBotMessages": "0",
        "notifyOnlyMyMessages": "0",
        "notifyOnlyFPMessages": "0",
        "notifyOnlyBotMessages": "0",
        "showImageName": "1"
    },

    "Greetings": {
        "ignoreSystemMessages": "0",
        "onlyNewChats": "0",
        "sendGreetings": "0",
        "greetingsText": "Привет, $chat_name!",
        "greetingsCooldown": "2"
    },

    "OrderConfirm": {
        "watermark": "1",
        "sendReply": "0",
        "replyText": "$username, спасибо за подтверждение заказа $order_id!\nЕсли не сложно, оставь, пожалуйста, отзыв!"
    },

    "ReviewReply": {
        "star1Reply": "0",
        "star2Reply": "0",
        "star3Reply": "0",
        "star4Reply": "0",
        "star5Reply": "0",
        "star1ReplyText": "",
        "star2ReplyText": "",
        "star3ReplyText": "",
        "star4ReplyText": "",
        "star5ReplyText": "",
    },

    "Proxy": {
        "enable": "0",
        "proxy": "",
        "check": "0"
    },

    "Other": {
        "watermark": "🐦",
        "requestsDelay": "4",
        "language": "ru"
    }
}


def create_configs():
    """Создает пустые файлы конфигов если их нет"""
    os.makedirs("configs", exist_ok=True)

    if not os.path.exists("configs/auto_response.cfg"):
        with open("configs/auto_response.cfg", "w", encoding="utf-8"):
            pass

    if not os.path.exists("configs/auto_delivery.cfg"):
        with open("configs/auto_delivery.cfg", "w", encoding="utf-8"):
            pass


def create_config_obj(settings) -> ConfigParser:
    """
    Создает объект конфига с нужными настройками.

    :param settings: dict настроек.

    :return: объект конфига.
    """
    config = ConfigParser(delimiters=(":",), interpolation=None)
    config.optionxform = str
    config.read_dict(settings)
    return config


def contains_russian(text: str) -> bool:
    for char in text:
        if 'А' <= char <= 'я' or char in 'Ёё':
            return True
    return False


def input_proxy(set_telebot_proxy: bool = False) -> str | None:
    return None


def setup_telegram_proxy():
    """Настройка прокси для Telegram (автоматическая версия)"""
    config = load_main_config("configs/_main.cfg")

    # Проверяем прокси из переменных окружения
    telegram_proxy = os.environ.get('TELEGRAM_PROXY', '')

    if telegram_proxy:
        try:
            scheme, login, password, ip, port = validate_proxy(telegram_proxy)
            proxy = build_proxy(scheme, login, password, ip, port)

            if check_proxy({"http": proxy, "https": proxy}):
                telebot.apihelper.proxy = {"http": proxy, "https": proxy}
                config.set("Telegram", "proxy", proxy)
                print(f"{Fore.GREEN}✓ Прокси для Telegram настроен{Style.RESET_ALL}")
        except Exception as ex:
            print(f"{Fore.RED}✗ Ошибка настройки прокси: {ex}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}Сохраняю конфиг...{Style.RESET_ALL}")
    with open("configs/_main.cfg", "w", encoding="utf-8") as f:
        config.write(f)
    time.sleep(2)


def first_setup():
    """Полностью автоматическая первичная настройка без ввода с терминала"""

    # Создаем необходимые директории и файлы
    os.makedirs("configs", exist_ok=True)
    os.makedirs("storage/cache", exist_ok=True)
    os.makedirs("storage/plugins", exist_ok=True)
    os.makedirs("storage/products", exist_ok=True)
    os.makedirs("plugins", exist_ok=True)

    create_configs()

    print(f"{Fore.CYAN}{Style.BRIGHT}Автоматическая настройка FunPay Cardinal...{Style.RESET_ALL}")
    time.sleep(1)

    # Создаем объект конфига
    config = create_config_obj(default_config)

    # ========== 1. Golden Key ==========
    golden_key = "kz1tpm50rgjatt52zxc5h43df91x0zk0"
    if len(golden_key) != 32:
        print(f"{Fore.RED}✗ Ошибка: Golden Key имеет неверную длину (нужно 32 символа){Style.RESET_ALL}")
        print(f"{Fore.RED}Получено: {len(golden_key)} символов{Style.RESET_ALL}")
        return False
    else:
        config.set("FunPay", "golden_key", golden_key)
        print(f"{Fore.GREEN}✓ Golden Key установлен{Style.RESET_ALL}")

    # ========== 2. User-Agent (оставляем стандартный) ==========
    print(f"{Fore.GREEN}✓ Использую стандартный User-Agent{Style.RESET_ALL}")

    # ========== 3. Telegram прокси (опционально) ==========
    telegram_proxy = os.environ.get('TELEGRAM_PROXY', '')
    if telegram_proxy:
        try:
            scheme, login, password, ip, port = validate_proxy(telegram_proxy)
            proxy = build_proxy(scheme, login, password, ip, port)
            if check_proxy({"http": proxy, "https": proxy}):
                config.set("Telegram", "proxy", proxy)
                print(f"{Fore.GREEN}✓ Telegram прокси настроен{Style.RESET_ALL}")
        except Exception as ex:
            print(f"{Fore.YELLOW}⚠ Предупреждение: не удалось настроить прокси: {ex}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}✓ Прокси для Telegram не требуется{Style.RESET_ALL}")

    # ========== 4. Telegram Bot Token ==========
    token = "8704132106:AAEujgCsNca1X38bmxRGguVQ4ft4I5ECYgE"
    username = None
    try:
        if not token or not token.split(":")[0].isdigit():
            raise Exception("Неправильный формат токена")

        # Проверяем токен (с таймаутом)
        bot = telebot.TeleBot(token)
        bot.get_me()
        username = bot.get_me().username

        if not username.lower().startswith("funpay"):
            print(f"{Fore.YELLOW}⚠ Предупреждение: username бота не начинается с 'funpay' (@{username}){Style.RESET_ALL}")

        config.set("Telegram", "token", token)
        config.set("Telegram", "enabled", "1")
        print(f"{Fore.GREEN}✓ Telegram токен установлен (бот: @{username}){Style.RESET_ALL}")
    except Exception as ex:
        print(f"{Fore.RED}✗ Ошибка при проверке токена бота: {ex}{Style.RESET_ALL}")
        return False

    # ========== 5. Пароль для входа ==========
    import random
    import string

    password = os.environ.get('BOT_PASSWORD', '')
    if not password:
        # Генерируем случайный пароль
        chars = string.ascii_letters + string.digits
        password = ''.join(random.choice(chars) for _ in range(12))
        print(f"{Fore.YELLOW}⚠ Сгенерирован случайный пароль: {password}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠ Сохраните его! Пароль можно будет сменить в боте командой /settings{Style.RESET_ALL}")

    if len(password) < 8:
        print(f"{Fore.YELLOW}⚠ Пароль слишком короткий, дополняю...{Style.RESET_ALL}")
        password = password + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8 - len(password)))

    config.set("Telegram", "secretKeyHash", hash_password(password))
    print(f"{Fore.GREEN}✓ Пароль для входа установлен{Style.RESET_ALL}")

    # ========== 6. FunPay прокси (опционально) ==========
    funpay_proxy = os.environ.get('FUNPAY_PROXY', '')
    if funpay_proxy:
        try:
            scheme, login, password, ip, port = validate_proxy(funpay_proxy)
            proxy = build_proxy(scheme, login, password, ip, port)
            if check_proxy({"http": proxy, "https": proxy}):
                config.set("Proxy", "proxy", proxy)
                config.set("Proxy", "enable", "1")
                config.set("Proxy", "check", "1")
                print(f"{Fore.GREEN}✓ FunPay прокси настроен{Style.RESET_ALL}")
        except Exception as ex:
            print(f"{Fore.YELLOW}⚠ Предупреждение: не удалось настроить FunPay прокси: {ex}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}✓ Прокси для FunPay не требуется{Style.RESET_ALL}")

    # ========== 7. Сохраняем конфиг ==========
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Сохраняю конфигурацию...{Style.RESET_ALL}")

    with open("configs/_main.cfg", "w", encoding="utf-8") as f:
        config.write(f)

    # Создаем файл с паролем для информации (опционально)
    password_file = "storage/password.txt"
    with open(password_file, "w", encoding="utf-8") as f:
        f.write(f"Пароль для входа в Telegram бота: {password}\n")
        f.write("Вы можете изменить его в боте командой /settings\n")

    print(f"{Fore.GREEN}✓ Конфигурация сохранена{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Пароль сохранен в {password_file}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{Style.BRIGHT}========================================{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}Автоматическая настройка завершена успешно!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}========================================{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Запущенные параметры:{Style.RESET_ALL}")
    print(f"  • Golden Key: {golden_key[:8]}...{golden_key[-8:]}")
    print(f"  • Telegram Bot: @{username if username else 'unknown'}")
    print(f"  • Пароль: {password}")
    print(f"\n{Fore.GREEN}Бот будет запущен автоматически...{Style.RESET_ALL}")

    time.sleep(3)
    return True
