import requests
from lxml import etree
from prettytable import PrettyTable
import re
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