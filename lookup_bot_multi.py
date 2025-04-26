import os
from dotenv import load_dotenv
import telebot
from telebot.apihelper import ApiTelegramException
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ————— Завантажити змінні оточення з .env —————
load_dotenv()

BOT_TOKEN       = os.getenv("BOT_TOKEN")
SPREADSHEET_ID  = os.getenv("SPREADSHEET_ID")
CREDS_FILE      = os.getenv("CREDS_FILE", "micro-edge-457711-t2-760a03863d1d.json")
EMBLEM_DIR      = os.getenv("EMBLEM_DIR", "emblems")

if not BOT_TOKEN or not SPREADSHEET_ID:
    raise RuntimeError("❌ Не задані BOT_TOKEN або SPREADSHEET_ID у файлі .env")

# ————— Конфіг для бот-логіки —————
GROUP_SHEETS = {
    -1001499325758: 'kids',
    -1001688878644: 'sundaygames',
}
# ——————————————————————————————

bot = telebot.TeleBot(BOT_TOKEN)

# Підключення до Google Sheets
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
gc    = gspread.authorize(creds)
sh    = gc.open_by_key(SPREADSHEET_ID)

# Завантажуємо дані для кожної групи
data_maps = {}
places    = {}
for chat_id, sheet_name in GROUP_SHEETS.items():
    ws     = sh.worksheet(sheet_name)
    rows   = ws.get_all_values()
    header = [h.strip() for h in rows[0]]
    try:
        nick_i   = header.index('Nickname')
        points_i = header.index('Points')
    except ValueError:
        raise RuntimeError(f"У аркуші '{sheet_name}' мають бути колонки 'Nickname' та 'Points'.")

    dm       = {}
    pts_list = []
    for row in rows[1:]:
        nick = row[nick_i].strip()
        if not nick:
            continue
        try:
            pts = int(row[points_i])
        except:
            pts = 0
        dm[nick.lower()] = pts
        pts_list.append(pts)

    pts_list.sort(reverse=True)
    data_maps[chat_id] = dm
    places[chat_id]    = pts_list

print("✅ Loaded GROUP_SHEETS:", GROUP_SHEETS)

# /start
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    if msg.chat.type in ['group', 'supergroup']:
        bot.reply_to(
            msg,
            "❗ Щоб отримати свій результат, напиши мені в особисті: t.me/Петро та натисни /start"
        )
    else:
        bot.send_message(
            msg.chat.id,
            "Привіт! Надішли свій нікнейм — і я скажу, скільки у тебе очок, твій ранг та місце в таблиці."
        )

# Основний хендлер
@bot.message_handler(func=lambda m: True, content_types=['text'])
def find_score(m):
    if m.text.startswith('/'):
        return

    cid = m.chat.id
    if cid not in data_maps:
        return

    nick = m.text.strip()
    key  = nick.lower()
    dm   = data_maps[cid]

    if key in dm:
        pts      = dm[key]
        pts_list = places[cid]
        total    = len(pts_list)
        place    = pts_list.index(pts) + 1

        # вибір рангу та емблеми
        if pts < 200:
            emblem_file = 'd_rank.png'
            rank_name   = 'D-ранг (0–199) — Новачок, свіжа кров - нубасік. Грай більше!'
        elif pts < 500:
            emblem_file = 'c_rank.png'
            rank_name   = 'C-ранг (200–499) — Видно, що Ти часто граєш. Часто ≠ вмієш. Тренуйся!'
        elif pts < 800:
            emblem_file = 'b_rank.png'
            rank_name   = 'B-ранг (500–799) — Оооо, бачу Ти вирвався в люди. Моя повага!'
        elif pts < 1200:
            emblem_file = 'a_rank.png'
            rank_name   = 'A-ранг (800–1199) — Чи можу я Вас благати стати моїм сенсеєм?'
        else:
            emblem_file = 's_rank.png'
            rank_name   = 'S-ранг (1200+) — Ви — справжня ЛЕГЕНДА!'

        caption = (
            f"✅ {nick} має {pts} очок (місце {place} з {total}).\n"
            f"{rank_name}"
        )
        emblem_path = os.path.join(EMBLEM_DIR, emblem_file)

        if m.chat.type in ['group', 'supergroup']:
            try:
                bot.delete_message(cid, m.message_id)
            except:
                pass

            with open(emblem_path, 'rb') as img:
                try:
                    bot.send_photo(m.from_user.id, img, caption=caption)
                except ApiTelegramException as e:
                    if "bot can't initiate conversation" in str(e):
                        bot.send_message(
                            cid,
                            "❗ Відкрий мій приватний чат і натисни /start: t.me/Петро"
                        )
                    else:
                        raise
        else:
            with open(emblem_path, 'rb') as img:
                bot.send_photo(cid, img, caption=caption)
    else:
        try:
            bot.delete_message(cid, m.message_id)
        except:
            pass
        bot.send_message(m.from_user.id, f'❌ Гравця "{nick}" не знайдено.')

# Запуск бота
bot.polling(none_stop=True)
