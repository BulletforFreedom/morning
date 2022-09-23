from datetime import date, datetime, timedelta
import math
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage
import requests
import os
import random
import chinese_calendar
from bs4 import BeautifulSoup as BS

nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d")  # 今天的日期

start_date = os.getenv('START_DATE')
city = os.getenv('CITY')
birthday = os.getenv('BIRTHDAY')

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')

if app_id is None or app_secret is None:
    print('请设置 APP_ID 和 APP_SECRET')
    exit(422)

if not user_ids:
    print('请设置 USER_ID，若存在多个 ID 用回车分开')
    exit(422)

if template_id is None:
    print('请设置 TEMPLATE_ID')
    exit(422)


# 获取指定日期节假日
def get_rest_day(start_time, end_time):
    hd = chinese_calendar.get_holidays(start_time, end_time)
    return hd


# 获取指定日期节假日
def get_rest_left():
    delta_date_int = 7
    # while (1):
    delta_date = timedelta(days=delta_date_int)
    end_time = today + delta_date
    rest_day = get_rest_day(today, end_time)
    if rest_day:
        rest_left = (rest_day[0] - today.date()).days
        return rest_left


# 获取指定月份节假日
def get_holidays(year, month):
    print(year)
    print(month)
    print(111111111111)
    holidays_name = ['春节', '元旦', '除夕', '元宵节', '清明节', '劳动节', '端午节', '中秋节', '国庆节']
    url = f"https://www.rili.com.cn/wannianli/{year}/{month}/"
    content = requests.get(url)
    bs = BS(content.text, "lxml")

    tds = bs.find("table").find("table").find_all("td")

    for td in tds:
        if 'noby' in td['class']:
            continue

        td = td.select(".riwai")
        if len(td) > 0:
            td = td[0].select("a")
        else:
            continue

        if len(td) > 1:
            day = td[0].text
            name = td[1].text
        else:
            continue

        if name in holidays_name and (int(day) > today.day or month != today.month):
            return name, f"{year}-{month}-{day}"
    return '', 0


# 获取法定节假日倒计时
def get_holidays_left():
    for year in range(today.year, today.year + 2):
        if year == today.year:
            start_month = today.month
        else:
            start_month = 1
        for month in range(start_month, 13):
            holiday_, date_ = get_holidays(year, month)
            print(holiday_)
            if date_:
                date_ = datetime.strptime(date_, "%Y-%m-%d")
                return {holiday_: (date_ - today).days}
            else:
                continue
    return {}


# weather 直接返回对象，在使用的地方用字段进行调用。
def get_weather():
    if city is None:
        print('请设置城市')
        return None
    url = "http://autodev.openspeech.cn/csp/api/v2.1/weather?openId=aiuicus&clientType=android&sign=android&city=" + city
    res = requests.get(url).json()
    if res is None:
        return None
    weather = res['data']['list'][0]
    return weather


# 获取当前日期为星期几
def get_week_day():
    week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    week_day = week_list[datetime.date(today).weekday()]
    return week_day


# 纪念日正数
def get_memorial_days_count():
    delta = today - datetime.strptime('2014-05-12', "%Y-%m-%d")
    return delta.days


# 生日倒计时
def get_birthday_left():
    if birthday is None:
        print('没有设置 BIRTHDAY')
        return 0
    next = datetime.strptime(str(today.year) + "-" + birthday, "%Y-%m-%d")
    if next < nowtime:
        next = next.replace(year=next.year + 1)
    return (next - today).days


# 彩虹屁 接口不稳定，所以失败的话会重新调用，直到成功
def get_words():
    words = requests.get("https://api.shadiao.pro/chp")
    if words.status_code != 200:
        return get_words()
    return words.json()['data']['text']


def format_temperature(temperature):
    return math.floor(temperature)


# 随机颜色
def get_random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


try:
    client = WeChatClient(app_id, app_secret)
except WeChatClientException as e:
    print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
    exit(502)

wm = WeChatMessage(client)
weather = get_weather()
holiday, days_left = get_holidays_left().popitem()
if weather is None:
    print('获取天气失败')
    exit(422)
data = {
    "city": {
        "value": city,
        "color": get_random_color()
    },
    "date": {
        "value": today.strftime('%Y年%m月%d日'),
        "color": get_random_color()
    },
    "week_day": {
        "value": get_week_day(),
        "color": get_random_color()
    },
    "weather": {
        "value": weather['weather'],
        "color": get_random_color()
    },
    "humidity": {
        "value": weather['humidity'],
        "color": get_random_color()
    },
    "wind": {
        "value": weather['wind'],
        "color": get_random_color()
    },
    "air_data": {
        "value": weather['airData'],
        "color": get_random_color()
    },
    "air_quality": {
        "value": weather['airQuality'],
        "color": get_random_color()
    },
    "temperature": {
        "value": math.floor(weather['temp']),
        "color": get_random_color()
    },
    "highest": {
        "value": math.floor(weather['high']),
        "color": get_random_color()
    },
    "lowest": {
        "value": math.floor(weather['low']),
        "color": get_random_color()
    },
    "rest_left": {
        "value": get_rest_left(),
        "color": get_random_color()
    },
    "holiday_name": {
        "value": holiday,
        "color": get_random_color()
    },
    "holiday_left": {
        "value": days_left,
        "color": get_random_color()
    },
    "love_days": {
        "value": get_memorial_days_count(),
        "color": get_random_color()
    },
    "words": {
        "value": get_words(),
        "color": get_random_color()
    },
}

if __name__ == '__main__':
    count = 0
    try:
        for user_id in user_ids:
            res = wm.send_template(user_id, template_id, data)
            count += 1
    except WeChatClientException as e:
        print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
        exit(502)

    print("发送了" + str(count) + "条消息")
