from __future__ import annotations

import os
import json
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING
    from cardinal import Cardinal

from logging import getLogger
from threading import Thread
from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B

from tg_bot import utils

NAME = Stars Auto Notification
VERSION = 1.0.0
DESCRIPTION = Авто-уведомления о заказах на звезды с Telegram со ссылкой на GGSel
CREDITS = @sidor0912
UUID = stars-auto-notify-9f8e-4d2a-8b6c-1e5f7a9d3c2b
SETTINGS_PAGE = False

logger = getLogger(FPC.stars_notify)

# Настройки плагина
settings = {
    enabled True,                     # Включен ли плагин
    ggsel_product_url ,             # Базовая ссылка на товар GGsel
    auto_fill_username True,          # Автоматически подставлять username в ссылку
    send_to_buyer False,              # Отправлять ли ссылку покупателю автоматически
    default_stars_amount 100,         # Количество звезд по умолчанию
    price_per_100_stars 0.5,          # Цена за 100 звезд (для уведомления)
    notification_chat_id None,        # ID чата для уведомлений (None = текущий чат)
}

SETTINGS_FILE = storagepluginsstars_notify_settings.json


def save_settings() - None
    Сохраняет настройки в файл
    os.makedirs(storageplugins, exist_ok=True)
    with open(SETTINGS_FILE, w, encoding=utf-8) as f
        json.dump(settings, f, indent=4, ensure_ascii=False)


def load_settings() - None
    Загружает настройки из файла
    global settings
    if os.path.exists(SETTINGS_FILE)
        try
            with open(SETTINGS_FILE, r, encoding=utf-8) as f
                saved = json.load(f)
                settings.update(saved)
                logger.info([STARS NOTIFY] Настройки загружены)
        except Exception as e
            logger.error(fОшибка загрузки настроек {e})


def get_ggsel_link(username str = None, amount int = None) - str
    
    Формирует ссылку на GGSel

    param username username покупателя (для авто-заполнения)
    param amount количество звезд
    return готовая ссылка
    
    base_url = settings.get(ggsel_product_url, )

    if not base_url
        return ⚠️ Ссылка на товар не настроена! Используйте stars_set_url

    # Если нужно подставить username в ссылку
    if settings.get(auto_fill_username, True) and username
        # Пробуем подставить username в ссылку
        if  in base_url
            base_url += f&username={username}
        else
            base_url += fusername={username}

    # Если нужно подставить количество
    if amount
        if  in base_url
            base_url += f&amount={amount}
        else
            base_url += famount={amount}

    return base_url


def format_notification_text(order, stars_amount int = None, price float = None) - str
    
    Форматирует текст уведомления

    param order объект заказа
    param stars_amount количество звезд
    param price цена
    return форматированный текст
    
    if stars_amount is None
        stars_amount = order.amount or settings.get(default_stars_amount, 100)

    if price is None
        price_per_100 = settings.get(price_per_100_stars, 0.5)
        price = round((stars_amount  100)  price_per_100, 2)

    link = get_ggsel_link(order.buyer_username, stars_amount)

    text = (
        f⭐️ bНОВЫЙ ЗАКАЗ НА ЗВЕЗДЫ!b ⭐️nn
        f👤 bПокупательb code{order.buyer_username}coden
        f🆔 bID заказаb code{order.id}coden
        f💰 bСуммаb code{order.price} {order.currency}coden
        f⭐️ bЗвездb code{stars_amount}coden
        f💵 bЦена на GGselb ~code{price}$codenn
        f🔗 bСсылка для покупкиbn
        fcode{link}codenn
        f📋 bИнструкцияbn
        f1️⃣ Откройте ссылку вышеn
        f2️⃣ Купите звезды (username уже подставлен)n
        f3️⃣ Нажмите кнопку «Подтвердить выполнение» на FunPay
    )

    return text


def send_notification(cardinal Cardinal, order, stars_amount int = None) - None
    
    Отправляет уведомление о заказе

    param cardinal экземпляр Кардинала
    param order объект заказа
    param stars_amount количество звезд
    
    if not cardinal.telegram
        logger.warning([STARS NOTIFY] Telegram не инициализирован)
        return

    tg = cardinal.telegram
    chat_id = settings.get(notification_chat_id)

    # Если не указан конкретный чат, отправляем в тот, откуда пришла команда
    # или в первый доступный
    if not chat_id
        # Пробуем получить первый диалог с ботом
        try
            updates = tg.bot.get_updates(limit=1, timeout=1)
            if updates
                chat_id = updates[0].message.chat.id
        except
            chat_id = None

    if not chat_id
        logger.error([STARS NOTIFY] Не удалось определить чат для уведомления)
        return

    text = format_notification_text(order, stars_amount)

    # Клавиатура для быстрых действий
    keyboard = K()
    keyboard.row(
        B(⭐️ Купить звезды, url=get_ggsel_link(order.buyer_username, stars_amount))
    )
    keyboard.row(
        B(✅ Подтвердить заказ, callback_data=fstars_confirm_{order.id}),
        B(💬 Написать买家, callback_data=fstars_chat_{order.id})
    )
    keyboard.row(
        B(📋 Скопировать ссылку, callback_data=fstars_copy_{order.id})
    )

    try
        tg.bot.send_message(
            chat_id,
            text,
            parse_mode=HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        logger.info(f[STARS NOTIFY] Уведомление о заказе #{order.id} отправлено)
    except Exception as e
        logger.error(f[STARS NOTIFY] Ошибка отправки уведомления {e})


def init_handlers(cardinal Cardinal) - None
    Инициализация обработчиков
    if not cardinal.telegram
        return

    load_settings()
    tg = cardinal.telegram
    bot = cardinal.telegram.bot

    # ==================== ОСНОВНОЙ ОБРАБОТЧИК ЗАКАЗОВ ====================

    @cardinal.new_order_handlers.append
    def on_new_order(cardinal Cardinal, event) - None
        Обработчик новых заказов
        if not settings.get(enabled, True)
            return

        order = event.order

        # Проверяем, что заказ на звезды
        order_desc = order.description.lower() if order.description else 
        keywords = [звезд, stars, ⭐️, звёзд, star]

        is_stars_order = any(keyword in order_desc for keyword in keywords)

        if not is_stars_order
            return

        # Определяем количество звезд
        stars_amount = order.amount
        if not stars_amount or stars_amount  1
            # Пробуем спарсить из описания
            import re
            match = re.search(r'(d+)s(штзвездstarsштук)', order_desc, re.IGNORECASE)
            if match
                stars_amount = int(match.group(1))
            else
                stars_amount = settings.get(default_stars_amount, 100)

        # Отправляем уведомление
        Thread(target=send_notification, args=(cardinal, order, stars_amount), daemon=True).start()

    # ==================== КОМАНДЫ НАСТРОЙКИ ====================

    @bot.message_handler(commands=[stars_enable])
    def cmd_enable(m)
        settings[enabled] = True
        save_settings()
        bot.send_message(m.chat.id, ✅ Плагин уведомлений о звездах ВКЛЮЧЕН)

    @bot.message_handler(commands=[stars_disable])
    def cmd_disable(m)
        settings[enabled] = False
        save_settings()
        bot.send_message(m.chat.id, ❌ Плагин уведомлений о звездах ВЫКЛЮЧЕН)

    @bot.message_handler(commands=[stars_set_url])
    def cmd_set_url(m)
        parts = m.text.split(maxsplit=1)
        if len(parts)  2
            bot.send_message(
                m.chat.id,
                ❌ Укажите ссылку на товар GGSelnn
                Пример stars_set_url httpsggsel.netcatalogproductavtopopolnenie-24-7-telegram-zvezdy-po-username-102083695
            )
            return

        url = parts[1].strip()
        settings[ggsel_product_url] = url
        save_settings()
        bot.send_message(
            m.chat.id,
            f✅ Ссылка на товар сохраненаncode{url}codenn
            fАвто-подстановка username {'✅' if settings['auto_fill_username'] else '❌'},
            parse_mode=HTML
        )

    @bot.message_handler(commands=[stars_toggle_autofill])
    def cmd_toggle_autofill(m)
        settings[auto_fill_username] = not settings.get(auto_fill_username, True)
        save_settings()
        status = включена if settings[auto_fill_username] else выключена
        bot.send_message(m.chat.id, f✅ Авто-подстановка username {status})

    @bot.message_handler(commands=[stars_set_price])
    def cmd_set_price(m)
        parts = m.text.split()
        if len(parts) != 2
            bot.send_message(
                m.chat.id,
                ❌ Укажите цену за 100 звезд в долларахnn
                Пример stars_set_price 0.5
            )
            return

        try
            price = float(parts[1])
            settings[price_per_100_stars] = price
            save_settings()
            bot.send_message(m.chat.id, f✅ Цена за 100 звезд ${price})
        except ValueError
            bot.send_message(m.chat.id, ❌ Цена должна быть числом)

    @bot.message_handler(commands=[stars_set_default_amount])
    def cmd_set_default_amount(m)
        parts = m.text.split()
        if len(parts) != 2
            bot.send_message(m.chat.id, ❌ Укажите количество звезд по умолчаниюnnПример stars_set_default_amount 100)
            return

        try
            amount = int(parts[1])
            settings[default_stars_amount] = amount
            save_settings()
            bot.send_message(m.chat.id, f✅ Количество звезд по умолчанию {amount})
        except ValueError
            bot.send_message(m.chat.id, ❌ Количество должно быть числом)

    @bot.message_handler(commands=[stars_set_chat])
    def cmd_set_chat(m)
        Устанавливает текущий чат для получения уведомлений
        settings[notification_chat_id] = m.chat.id
        save_settings()
        bot.send_message(m.chat.id, ✅ Уведомления будут приходить в этот чат)

    @bot.message_handler(commands=[stars_send_to_buyer])
    def cmd_toggle_send_to_buyer(m)
        settings[send_to_buyer] = not settings.get(send_to_buyer, False)
        save_settings()
        status = включена if settings[send_to_buyer] else выключена
        bot.send_message(
            m.chat.id,
            f✅ Автоматическая отправка ссылки покупателю {status}nn
            f⚠️ Внимание! При включении этой опции ссылка на GGsel будет отправляться покупателю автоматически.
        )

    @bot.message_handler(commands=[stars_status])
    def cmd_status(m)
        status = 🟢 ВКЛЮЧЕН if settings.get(enabled, True) else 🔴 ВЫКЛЮЧЕН
        url = settings.get(ggsel_product_url, ❌ НЕ УСТАНОВЛЕН)
        autofill = ✅ Да if settings.get(auto_fill_username, True) else ❌ Нет
        price = settings.get(price_per_100_stars, 0.5)
        default_amount = settings.get(default_stars_amount, 100)
        send_to_buyer = ✅ Да if settings.get(send_to_buyer, False) else ❌ Нет

        text = (
            f⭐️ bStars Auto Notificationb ⭐️nn
            fbСтатусb {status}n
            fbСсылка на товарbncode{url[80]}...coden
            fbАвто-подстановка usernameb {autofill}n
            fbЦена за 100 звездb ${price}n
            fbЗвезд по умолчаниюb {default_amount}n
            fbОтправлять ссылку покупателюb {send_to_buyer}nn
            f📋 bДоступные командыbn
            fstars_enable - включить плагинn
            fstars_disable - выключить плагинn
            fstars_set_url url - установить ссылку на товарn
            fstars_toggle_autofill - вклвыкл подстановку usernamen
            fstars_set_price цена - цена за 100 звездn
            fstars_set_default_amount кол-во - звезд по умолчаниюn
            fstars_set_chat - установить чат для уведомленийn
            fstars_send_to_buyer - вклвыкл отправку ссылки покупателюn
            fstars_test - тестовое уведомление
        )

        bot.send_message(m.chat.id, text, parse_mode=HTML, disable_web_page_preview=True)

    @bot.message_handler(commands=[stars_test])
    def cmd_test(m)
        Тестовое уведомление
        # Создаем тестовый объект заказа
        class TestOrder
            id = TEST12345678
            buyer_username = test_user
            price = 1.0
            currency = ₽
            amount = 100
            description = Тестовый заказ на 100 звезд

        test_order = TestOrder()

        text = format_notification_text(test_order)

        keyboard = K()
        keyboard.row(
            B(⭐️ Купить звезды, url=get_ggsel_link(test_user, 100))
        )

        bot.send_message(
            m.chat.id,
            text,
            parse_mode=HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        bot.send_message(m.chat.id, ✅ Тестовое уведомление отправлено)

    # ==================== CALLBACK ОБРАБОТЧИКИ ====================

    @tg.cb_handler(func=lambda c c.data.startswith(stars_confirm_))
    def confirm_order_callback(c)
        order_id = c.data.replace(stars_confirm_, )
        bot.answer_callback_query(c.id, fПодтвердите заказ #{order_id} вручную на FunPay)
        bot.send_message(c.message.chat.id, f🔄 Не забудьте подтвердить заказ #{order_id} на FunPay!)

    @tg.cb_handler(func=lambda c c.data.startswith(stars_chat_))
    def chat_callback(c)
        order_id = c.data.replace(stars_chat_, )
        bot.answer_callback_query(c.id, Открываю диалог с покупателем...)
        bot.send_message(c.message.chat.id, f💬 Напишите покупателю вручную в чате FunPay. Заказ #{order_id})

    @tg.cb_handler(func=lambda c c.data.startswith(stars_copy_))
    def copy_link_callback(c)
        order_id = c.data.replace(stars_copy_, )
        # Пытаемся найти заказ в сохраненных
        link = get_ggsel_link(USERNAME, 100)
        bot.answer_callback_query(c.id, fСсылка {link}, show_alert=True)

    # Регистрируем команды
    cardinal.add_telegram_commands(UUID, [
        (stars_enable, ⭐️ включить уведомления о звездах, True),
        (stars_disable, ⭐️ выключить уведомления о звездах, True),
        (stars_set_url, ⭐️ установить ссылку на товар GGSel, True),
        (stars_set_price, ⭐️ установить цену за 100 звезд, True),
        (stars_set_default_amount, ⭐️ установить кол-во звезд по умолчанию, True),
        (stars_set_chat, ⭐️ установить чат для уведомлений, True),
        (stars_toggle_autofill, ⭐️ вклвыкл подстановку username, True),
        (stars_send_to_buyer, ⭐️ вклвыкл отправку ссылки покупателю, True),
        (stars_status, ⭐️ статус плагина, True),
        (stars_test, ⭐️ тестовое уведомление, True),
    ])


BIND_TO_POST_INIT = [init_handlers]
BIND_TO_DELETE = None