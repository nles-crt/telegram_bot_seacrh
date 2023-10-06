import datetime
import telegram
import time
import re
import utils.func as func
from database.user_database import UserDatabase
from database.telegram_url_database import TelegramURLDatabase
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, filters,CallbackQueryHandler
from telegram.ext import *
from telegram.constants import ParseMode

user_db = UserDatabase()
tele_url_db = TelegramURLDatabase()

last_page_click = {}
admin_user = [6191802331]



async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username
    if user_db.user_exists(user_id):
        await context.bot.send_message(chat_id=update.message.chat_id, text="你的信息存在数据库输入/help查看命令吧")
    else:
        user_db.add_user(user_id,username)
        await context.bot.send_message(chat_id=update.message.chat_id, text="已经注册输入/help 查看命令吧")
async def help(update: Update, context: CallbackContext):
    help_text = """
    📋 可用的命令和功能如下:
    /start - 开始使用机器人并完成注册.
    /add url - 将一个超酷的URL添加到数据库中.

    💡 想知道怎么使用吗?很简单!只需按照以下方式操作:

    使用 /start 命令进行注册,然后就可以开始畅游机器人的世界啦!
    想分享一个酷炫的URL?使用 /add 命令,然后附上URL,它会被添加到我们的数据库中.
    🙋‍♂️ 如果有任何问题或需要帮助,请随时与我们联系!我们随时待命,准备为你提供支持和答疑解惑.🤝 #机器人 #帮助 #指南
    """

    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def add_url(update: Update, context: CallbackContext):
    user_message = update.message.text

    # 检查用户消息是否包含 URL
    if len(user_message.split()) <= 1:
        await context.bot.send_message(chat_id=update.message.chat_id, text="请输入 URL\n使用实例:/add https://t.me/GDP_sc")
        return

    vuln = user_message.split()[1]

    # 检查记录是否已经存在
    if tele_url_db.search_record_by_telegram_url(vuln):
        await context.bot.send_message(chat_id=update.message.chat_id, text="记录已经存在")
    else:
        try:
            # 获取 Telegram 信息
            info = func.get_telegram_info(vuln)
            if info:
                url, title, members_count, group_type = info
                current_date = datetime.date.today()
                formatted_date = current_date.strftime("%Y-%m-%d")
                
                # 插入记录
                tele_url_db.insert_record(title, url, group_type, formatted_date, members_count)

                await context.bot.send_message(chat_id=update.message.chat_id, text="添加成功")
            else:
                await context.bot.send_message(chat_id=update.message.chat_id, text="无法获取信息")
        except Exception as e:
            # 处理异常情况
            await context.bot.send_message(chat_id=update.message.chat_id, text=f"添加 URL 时发生异常: {str(e)}")


async def managementInformation(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    user_message = update.message.text
    if user_id in admin_user:
        command, args, *vuln = user_message.split()
        if command == '/admin' and args:
            if args == "s":
                limit = vuln[0] if vuln else 10
                user_data = func.parse_user_data(user_db.get_user_info_all(limit))
                print(user_data)
                await context.bot.send_message(chat_id=user_id, text=f"{user_data}")
            elif args == "u":
                if vuln:
                        administrator_Notifications = vuln[0]
                        user_data = func.parse_query_result_to_dict(user_db.get_user_info_all(limit=None))
                        print(user_data)
                        for user_info in user_data:
                            try:
                                user_id = user_info.get('id')
                                await context.bot.send_message(chat_id=user_id, text=f"{administrator_Notifications}")
                            except Exception as e:
                                print(f"发送消息失败: {e}")
                                await context.bot.send_message(chat_id=admin_user[0], text=f"被{user_id}拉黑")


                else:
                    await context.bot.send_message(chat_id=user_id, text=f"请输入发送内容")
            elif args == "logs":
                await context.bot.send_document(chat_id=admin_user[0], document=open("user_info.txt", "rb"),caption="user_info发送成功")
        else:
            await context.bot.send_message(chat_id=user_id, text="Invalid command format. Use '/admin [parameter]' to specify a parameter.")
    else:
        await context.bot.send_message(chat_id=user_id, text="You are not authorized to use this command.")

async def button_click(update, context):
    query = update.callback_query
    data = query.data
    name = context.user_data.get('name', '')
    i = context.user_data.get('i', 1)
    asname = context.user_data.get('asname', '')
    if asname != name:
        i = 1
    if data == "button1":
        if i > 1:
            i -= 1
    elif data == "button2":
        # 假设你有一种方式来检查是否还有更多数据,例如 has_more 变量
        has_more = True  # 你需要根据实际情况设置 has_more 的值
        if has_more:
            i += 1
    else:
        # 如果没有点击按钮,则默认i为1
        i = 1

    if not name:
        await query.answer(text="当前会话已经失效重新查询")
        return

    getdata, has_more = tele_url_db.search_users_by_name(name, page=i)
    getdata = func.organize_data(getdata)

    keyboard = [
        [InlineKeyboardButton(f"上一页", callback_data=f"button1")],
        [InlineKeyboardButton(f"下一页", callback_data=f"button2")],
    ]
    
    if i <= 1:
        keyboard.pop(0)
    
    if not has_more:
        keyboard.pop()

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"当前页码:{i}\n{getdata}"
    await query.message.edit_text(text=text, reply_markup=reply_markup, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)
    
    # 更新上一个 name 和当前 name 以及 i 值
    context.user_data['asname'] = name
    context.user_data['name'] = name
    context.user_data['i'] = i



async def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username
    context.user_data['name'] = user_message
    with open('user_info.txt', 'a') as file:
        file.write(f"User ID: {user_id}, User Name: {user_name}, User Message: {user_message}\n")
    data, lendata = tele_url_db.search_users_by_name(user_message,1)
    data = func.organize_data(data)
    if lendata:
        keyboard = [[
                     InlineKeyboardButton("下一页", callback_data="button2")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"当前页码:1\n{data}", disable_web_page_preview=True, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    elif len(data) == 0:
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"太可惜了没有相关频道和群聊", disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"{data}", disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)

async def error(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.message.chat_id, text="An error occurred. Please try again later.")
if __name__ == "__main__":
    token = '5639834148:AAGkn7UoGYVB8uMr6SbQzTnpOhjzWhAvOCk'
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("add", add_url))
    app.add_handler(CommandHandler("admin", managementInformation))
    app.add_handler(MessageHandler(None,handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()
