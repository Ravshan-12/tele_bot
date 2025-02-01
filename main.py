import telebot
import random
import time
from tinydb import TinyDB, Query
from datetime import datetime

TOKEN = "8094890103:AAHdT2MYY1QzJ7GLtm5K7eLNryTjg1vAuQk"
ADMIN_IDS = [5359507225]

bot = telebot.TeleBot(TOKEN)
db = TinyDB("database.json")
users = db.table("users")


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User-{user_id}"
    user = users.get(Query().id == user_id)

    if not user:
        users.insert({"id": user_id, "balance": 3000, "last_bonus": "", "username": username})
        bot.reply_to(message, "Xush kelibsiz! Sizga boshlang‘ich 3000 coin berildi! \n\n🎮 O‘yin: !b [coin miqdori]")
    else:
        bot.reply_to(message, "Siz allaqachon ro‘yxatdan o‘tgansiz! O‘yinni boshlash uchun !b [coin] ni yozing!")


@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = message.from_user.id
    user = users.get(Query().id == user_id)

    if user:
        bot.reply_to(message, f"💰 Sizning balansingiz: {user['balance']} coin")
    else:
        bot.reply_to(message, "🚨 Siz ro‘yxatdan o‘tmagansiz! /start ni bosing!")


@bot.message_handler(commands=['top'])
def top(message):
    all_users = sorted(users.all(), key=lambda x: x['balance'], reverse=True)[:10]
    leaderboard = "🏆 Eng yuqori balansga ega o‘yinchilar:\n"

    for i, user in enumerate(all_users, 1):
        # Telegram foydalanuvchisini username yoki first_name bilan ko'rsatish
        telegram_user = bot.get_chat_member(message.chat.id, user['id']).user
        nickname = telegram_user.username or telegram_user.first_name
        leaderboard += f"{i}. {nickname} - {user['balance']} coin\n"

    leaderboard += f"\n👥 Jami foydalanuvchilar: {len(users)}"
    bot.reply_to(message, leaderboard)


@bot.message_handler(commands=['daily_bonus'])
def daily_bonus(message):
    user_id = message.from_user.id
    user = users.get(Query().id == user_id)

    if user:
        last_bonus = user.get('last_bonus', "")
        today = datetime.now().strftime('%Y-%m-%d')

        if last_bonus == today:
            bot.reply_to(message, "⚠️ Siz bugungi bonusni oldingiz, ertagacha sabr qiling!")
        else:
            bonus = random.randint(3000, 5000)
            users.update({'balance': user['balance'] + bonus, 'last_bonus': today}, Query().id == user_id)
            bot.reply_to(message, f"🎉 Kunlik bonus! {bonus} coin qo‘shildi!")
    else:
        bot.reply_to(message, "🚨 Siz ro‘yxatdan o‘tmagansiz! /start ni bosing!")


@bot.message_handler(commands=['status'])
def status(message):
    user_id = message.from_user.id
    user = users.get(Query().id == user_id)

    if user:
        bot.reply_to(message,
                     f"📊 Sizning ma’lumotlaringiz:\n👤 Username: @{user['username']}\n💰 Balans: {user['balance']} coin")
    else:
        bot.reply_to(message, "🚨 Siz ro‘yxatdan o‘tmagansiz! /start ni bosing!")


@bot.message_handler(commands=['give'])
def give(message):
    # 1. Admin ekanligini tekshirish
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 Sizga bu buyruqni ishlatish huquqi yo‘q!")
        return

    try:
        # 2. Buyruq argumentlarini olish
        args = message.text.split()
        amount = int(args[1])

        # 3. Reply orqali foydalanuvchini tanlash
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = users.get(Query().id == user_id)

            # 4. Agar foydalanuvchi bazada bo‘lsa, coin qo‘shish
            if user:
                users.update({'balance': user['balance'] + amount}, Query().id == user_id)
                bot.reply_to(message, f"✅ {amount} coin @{message.reply_to_message.from_user.username} foydalanuvchiga berildi!")
            else:
                bot.reply_to(message, "🚨 Foydalanuvchi bazada topilmadi!")
        else:
            bot.reply_to(message, "🚨 Iltimos, foydalanuvchini reply qilib yuboring!")

    except (IndexError, ValueError):
        bot.reply_to(message, "🚨 To‘g‘ri foydalanish: `/give [miqdor]` - Reply sifatida yozing!")



@bot.message_handler(commands=['delete'])
def delete(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "🚫 Sizga bu buyruqni ishlatish huquqi berilmagan!")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        users.update({'balance': 0}, Query().id == user_id)
        bot.reply_to(message, f"❌ @{message.reply_to_message.from_user.username} ning balansi 0 qilindi!")


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "📌 Buyruqlar ro‘yxati:\n\n"
                          "/start - O‘yinni boshlash\n"
                          "/balance - Balansni tekshirish\n"
                          "/top - Eng kuchli o‘yinchilar\n"
                          "/daily_bonus - Kunlik bonus olish\n"
                          "/status - Foydalanuvchi ma’lumotlari\n"
                          "/give - Coin berish\n"
                          "/delete - Admin uchun balansni 0 qilish\n"
                          "/help - Qo‘llanma")


@bot.message_handler(func=lambda message: message.text.startswith('!b'))
def basketball_game(message):
    user_id = message.from_user.id
    user = users.get(Query().id == user_id)

    if user:
        try:
            bet = int(message.text.split()[1])

            if bet > user['balance'] or bet <= 0:
                bot.reply_to(message, "🚨 Sizda yetarli coin yo‘q yoki noto‘g‘ri miqdor!")
                return

            dice_msg = bot.send_dice(message.chat.id, '🏀')
            time.sleep(3)

            if dice_msg.dice.value in [4, 5]:  # 4 - basket tushganda yutish
                win_amount = bet * random.randint(2, 3)
                users.update({'balance': user['balance'] + win_amount}, Query().id == user_id)
                bot.reply_to(message, f"🎉 G‘alaba! Siz {win_amount} coin yutdingiz! 🏆")
            else:
                users.update({'balance': user['balance'] - bet}, Query().id == user_id)
                bot.reply_to(message, "😢 Yutqazdingiz! Omadingizni yana sinab ko‘ring!")

        except:
            bot.reply_to(message, "🚨 To‘g‘ri foydalanish: !b [coin miqdori]")


@bot.message_handler(func=lambda message: message.text.startswith('!t'))
def stone_game(message):
    user_id = message.from_user.id
    user = users.get(Query().id == user_id)

    if user:
        try:
            bet = int(message.text.split()[1])

            if bet > user['balance'] or bet <= 0:
                bot.reply_to(message, "🚨 Sizda yetarli coin yo‘q yoki noto‘g‘ri miqdor!")
                return

            dice_msg = bot.send_dice(message.chat.id, '🎲')
            time.sleep(3)

            if dice_msg.dice.value == 6:  # 6 - tosh tushganda yutish
                win_amount = bet * 4  # 4x sovrin
                users.update({'balance': user['balance'] + win_amount}, Query().id == user_id)
                bot.reply_to(message, f"🎉 G‘alaba! Siz {win_amount} coin yutdingiz! 🎲")
            else:
                users.update({'balance': user['balance'] - bet}, Query().id == user_id)
                bot.reply_to(message, "😢 Yutqazdingiz! Omadingizni yana sinab ko‘ring!")

        except:
            bot.reply_to(message, "🚨 To‘g‘ri foydalanish: !t [coin miqdori]")

print("🤖 Bot ishga tushdi...")
bot.polling(none_stop=True)
