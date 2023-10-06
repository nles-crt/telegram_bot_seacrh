import datetime
import telegram

import sqlite3
import time
import re
import requests
from lxml import etree
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, filters,CallbackQueryHandler
from telegram.ext import *
from telegram.constants import ParseMode
from prettytable import PrettyTable

last_page_click = {}
admin_user = [6191802331]

def extract_members_prefix(text):
    """
    从文本中提取匹配 "members" 前面的所有数据.
    Args:
        text (str): 输入文本.

    Returns:
        str or None: 如果找到匹配的数据,返回提取的数据,否则返回 None.
    """
    match = re.search(r'(.+?)\s+members', text)
    if match:
        result = match.group(1).replace(" ", "")
        return result
    else:
        return None

def extract_all_numbers_as_string(text):
    """
    从文本中提取所有数字并连接成一个字符串.
    Args:
        text (str): 输入文本.

    Returns:
        str or None: 如果找到数字,返回连接后的字符串,否则返回 None.
    """
    pattern = r'\d+'
    matches = re.findall(pattern, text)
    if matches:
        return ''.join(matches)
    else:
        return None

def get_telegram_info(url):
    """
    发送请求并解析 Telegram 页面信息.
    Args:
        url (str): 要请求的 URL.

    Returns:
        None
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            response = etree.HTML(response.text)
            anonymous_groups = response.xpath('//a[@class="tgme_username_link"]')
            if anonymous_groups:
                return

            title = response.xpath('//span[@dir="auto"]/text()')[0]
            members_text = response.xpath('//div[@class="tgme_page_extra"]/text()')[0]
            
            if "subscribers" in members_text:
                group_type = "channel"
                members_count = extract_all_numbers_as_string(members_text)
            else:
                group_type = "supergroup"
                members_count = extract_members_prefix(members_text)
            
            return url, title, members_count, group_type
    except requests.exceptions.RequestException as e:
        return False



# Create UserDatabase class
class UserDatabase:
    def __init__(self, db_name='user_data.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_blacklisted INTEGER
            )
        ''')
        self.conn.commit()
    def get_user_info(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()
    
    def get_user_info_all(self, limit=10):
        query = 'SELECT * FROM users'
        if limit is not None:
            query += ' LIMIT ?'
            self.cursor.execute(query, (limit,))
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()
    
    
    def add_user(self, user_id, username):
        self.cursor.execute('INSERT INTO users (user_id, username, is_blacklisted) VALUES (?, ?, 0)', (user_id, username))
        self.conn.commit()
    
    def user_exists(self, user_id):
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result and result[0] > 0

    def is_blacklisted(self, user_id):
        self.cursor.execute('SELECT is_blacklisted FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result and result[0] == 1

    def blacklist_user(self, user_id):
        self.cursor.execute('UPDATE users SET is_blacklisted = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def unblacklist_user(self, user_id):
        self.cursor.execute('UPDATE users SET is_blacklisted = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
class TelegramURLDatabase:
    def __init__(self, db_name='telegram_URL.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        
    def search_users_by_name(self, name, page, page_size=10):
        offset = (page - 1) * page_size
        query = 'SELECT * FROM telegram WHERE name LIKE ? LIMIT ?, ?'
        self.cursor.execute(query, ('%' + name + '%', offset, page_size))
        results = self.cursor.fetchall()
        has_more = len(results) == page_size
        return results, has_more
    
    def insert_record(self, name, telegram_url, type, time, number):
        """
        向数据库中插入一条记录.
        
        Args:
            name (str): 名称.
            telegram_url (str): Telegram URL.
            type (str): 类型.
            time (str): 时间.
            number (str): 数字.
        """
        # 使用参数化查询来插入数据
        query = "INSERT INTO telegram (name, telegram_url, type, time, number) VALUES (?, ?, ?, ?, ?)"
        values = (name, telegram_url, type, time, number)
        self.cursor.execute(query, values)
        self.conn.commit()  # 修复此行,将self.connection改为self.conn
        return 
    def search_record_by_telegram_url(self, telegram_url):
        query = "SELECT * FROM telegram WHERE telegram_url = ?"
        self.cursor.execute(query, (telegram_url,))
        results = self.cursor.fetchone()
        return results
    def get_data_by_page_and_name(self, page_id, name):
        items_per_page = 10
        offset = (page_id - 1) * items_per_page
        query = 'SELECT * FROM telegram WHERE name LIKE ? LIMIT ?, ?'
        self.cursor.execute(query, ('%' + name + '%', offset, items_per_page))
        results = self.cursor.fetchall()
        return results

    def close(self):
        self.conn.close()

user_db = UserDatabase()
tele_url_db = TelegramURLDatabase()

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


def parse_query_result_to_dict(query_result):
    result_dicts = []
    for row in query_result:
        user_id, username, is_blacklisted = row
        if username is None:
            continue
        data_dict = {
            "id": user_id,
            "username": username,
            "is_blacklisted": bool(is_blacklisted)
        }
        result_dicts.append(data_dict)
    return result_dicts
def parse_user_data(user_data_list):
    i = 0
    table = PrettyTable()
    table.field_names = ["id", "用户名", "用户ID"]
    for user_tuple in user_data_list:
        user_id, username, is_blacklisted = user_tuple
        if username is None:
            continue
        i += 1
        table.add_row([i, f"@{username}", user_id])
    return str(table)
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
            info = get_telegram_info(vuln)
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
                user_data = parse_user_data(user_db.get_user_info_all(limit))
                print(user_data)
                await context.bot.send_message(chat_id=user_id, text=f"{user_data}")
            elif args == "u":
                if vuln:
                        administrator_Notifications = vuln[0]
                        user_data = parse_query_result_to_dict(user_db.get_user_info_all(limit=None))
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

def format_large_numbers(number):
    if number >= 1000:
        formatted_number = "{:.1f}k".format(number / 1000)
    else:
        formatted_number = str(number)
    return formatted_number

def organize_data(data_list):
    formatted_data = []
    for item in data_list:
        name, link, category, date, members = item
        members = format_large_numbers(members)
        if "channel" in category:
            category = "📢"
        else:
            category = "👥"
        formatted_entry = f"{category if category else 'N/A'}[{name} -{members if members else 'N/A'}]({link})"
        formatted_data.append(formatted_entry)
    result = '\n'.join(formatted_data)
    return result

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
    getdata = organize_data(getdata)

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
    data = organize_data(data)
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
