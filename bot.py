import datetime
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
from system import *
import time
user_last_click_time = {}

user_db = UserDatabase()
tele_url_db = TelegramURLDatabase()

def is_frequent_click(user_id, interval_seconds=5):
    """
    检查用户是否频繁点击按钮.

    参数:
    - user_id: 用户的唯一标识符.
    - interval_seconds: 两次点击之间的最小时间间隔(以秒为单位),默认为10秒.

    返回值:
    - True:用户频繁点击了按钮.
    - False:用户未频繁点击按钮.
    """
    if user_id in user_last_click_time:
        last_click_time = user_last_click_time[user_id]
        current_time = time.time()
        if current_time - last_click_time < interval_seconds:
            return True  # 用户频繁点击按钮
    
    # 记录最后一次点击时间
    user_last_click_time[user_id] = time.time()
    return False  # 用户未频繁点击按钮


async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username
    if user_db.user_exists(user_id):
        await update.message.reply_text(text="你的信息存在数据库输入/help查看命令吧")
    else:
        user_db.add_user(user_id,username)
        await update.message.reply_text(text="已经注册输入/help 查看命令吧")
async def help(update: Update, context: CallbackContext):
    help_text = """
📄公告当前机器人可任意群聊使用

=============================
禁止🈲🚫色情/暴力/儿童色情/钓鱼/引战/侵权
📣警告！如您所在地的国家/地区不允许您阅览此敏频道,请您关闭连接并退出机器人.
=============================
📋 可用的命令和功能如下:
/start - 开始使用机器人并完成注册.
/add url - 将一个的URL添加到数据库中.
/search 内容 - 在数据库中搜索相关内容.
---------------------------------------
使用默认搜索方式私聊机器人输入搜索内容即可
---------------------------------------
案例：/search 网络安全
---------------------------------------
群聊案例：/search@Testtherobotabcd_bot 网络安全 或 /search 网络安全
################################
测试群聊[https://t.me/testdogs]
意见反应群组 ---- @testdogs 
🙋‍♂️ 机器人还属于测试中. 🤝 #机器人 #帮助 #指南
    """

    await update.message.reply_text(help_text)

async def add_url(update: Update, context: CallbackContext):
    user_message = update.message.text

    # 检查用户消息是否包含 URL
    if len(user_message.split()) <= 1:
        await update.message.reply_text(text="请输入 URL\n使用实例:/add https://t.me/GDP_sc")
        return

    vuln = user_message.split()[1]

    # 检查记录是否已经存在
    if tele_url_db.search_record_by_telegram_url(vuln):
        await update.message.reply_text(text="记录已经存在")
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

                await update.message.reply_text(text="添加成功")
            else:
                await update.message.reply_text(text="无法获取信息")
        except Exception as e:
            # 处理异常情况
            await update.message.reply_text(text=f"添加 URL 时发生异常: {str(e)}")


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
    with open('user_info.txt', 'a+',encoding="utf8") as file:
        file.write(f"User ID: {user_id}, User Name: {user_name}, User Message: {user_message}\n")
    data, lendata = tele_url_db.search_users_by_name(user_message,1)
    data = func.organize_data(data)
    if lendata:
        keyboard = [[
                     InlineKeyboardButton("下一页", callback_data="button2")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"当前页码: 1\n{data}", disable_web_page_preview=True, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    elif len(data) == 0:
        await update.message.reply_text(text=f"太可惜了没有相关频道和群聊试试\n/search {user_message}")
    else:
        await update.message.reply_text(text=f"{data}", disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)


async def error(update: Update, context: CallbackContext):
    await update.message.reply_text(text="An error occurred. Please try again later.")


def create_pagination_keyboard(has_prev_page=True, has_next_page=True):
    """
    创建一个带有上一页和下一页按钮的键盘.

    :param has_prev_page: 是否包含上一页按钮
    :param has_next_page: 是否包含下一页按钮
    :return: 一个包含上一页和下一页按钮的InlineKeyboardMarkup对象
    """
    keyboard = []

    if has_prev_page:
        prev_button = InlineKeyboardButton("上一页", callback_data='prev_page')
        keyboard.append([prev_button])

    if has_next_page:
        next_button = InlineKeyboardButton("下一页", callback_data='next_page')
        keyboard.append([next_button])

    return InlineKeyboardMarkup(keyboard)


async def pagination_button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.callback_query.from_user.id
    if is_frequent_click(user_id):
        print("您点击得太频繁了,请稍后再试.",user_id)
        return
    message_id = query.message.message_id
    if data == 'prev_page':
            user_db.update_user_page(eid=message_id, operation=0)
    elif data == 'next_page':
            user_db.update_user_page(eid=message_id, operation=1)
    user_mid = user_db.get_user_page(message_id)
    if user_mid:
        kw, current_page, max_pages = user_mid[2], user_mid[1], user_mid[4]
        getdata, trueAndFalse, count = func.dict_to_markdown_links(func.get_data_for_kw_and_page(kw=kw, page=current_page))
        has_prev_page = current_page > 1
        has_next_page = current_page < max_pages
        reply_markup = create_pagination_keyboard(has_prev_page=has_prev_page, has_next_page=has_next_page)
        await query.message.edit_text(text=f"搜索内容:{user_mid[2]}\n{getdata}\n{user_mid[1]}/{count}", reply_markup=reply_markup, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)
    else:
        await query.message.edit_text(text=f"过期:{message_id}")


async def search(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username
    if len(user_message.split()) == 2:
        text = user_message.split()[1]
        data,trueAndFalse,count = func.dict_to_markdown_links(func.get_data_for_kw_and_page(text))
        if trueAndFalse:
            keyboard = create_pagination_keyboard(has_prev_page=False, has_next_page=True)
            message = await update.message.reply_text(text=f"搜索内容:{text}\n{data}\n当前页码为1/{count}", disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            message_id = message.message_id
            user_db.add_user_page(eid=message_id,text=text,pageid=1,type="all",count=count)
        else:
            await update.message.reply_text(text=data, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)
    else:
        print("非请求")
if __name__ == "__main__":
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("add", add_url))
    app.add_handler(CommandHandler("admin", managementInformation))
    app.add_handler(MessageHandler(None,handle_message))
# 添加 CallbackQueryHandler 处理程序,使用正则表达式模式匹配
    app.add_handler(CallbackQueryHandler(button_click, pattern=r'^button\d+$'))
    app.add_handler(CallbackQueryHandler(pagination_button_click, pattern=r'^(prev_page|next_page)$'))

    app.run_polling()
