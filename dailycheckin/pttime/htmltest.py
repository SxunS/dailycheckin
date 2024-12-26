import os
import unittest

from bs4 import BeautifulSoup


class MyTestCase(unittest.TestCase):


    def test_something(self):
        html_file_path = os.path.join(os.path.dirname(__file__), "tmp-success.html")

        # 读取HTML文件内容
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取用户信息
        user_info = soup.find('span', class_='medium left').text.strip()
        user_name = soup.find('a', class_='PowerUser_Name').text.strip()
        user_id = soup.find('a', class_='PowerUser_Name')['href'].split('=')[-1]

        # 提取签到记录
        attendance_info = soup.find('table', class_='mainouter mt5').findChild("td", class_="embedded")

        # 初始化变量
        total_days = 0
        consecutive_days = 0
        first_checkin = ''
        days_since_first_checkin = ''
        current_consecutive_start = ''
        checkin_records = []

        # 解析签到记录
        for span in attendance_info:
            text = span.text.strip()
            if '总签到：' in text:
                total_days = int(text.split('：')[1].split('天')[0])
            elif '连续天数：' in text:
                consecutive_days = int(text.split('：')[1].split('天')[0])
            elif '第一次签到：' in text:
                first_checkin = text.split('：')[1]
            elif '距今：' in text:
                days_since_first_checkin = text.split('：')[1]
            elif '本次连续签到开始时间：' in text:
                current_consecutive_start = text.split('：')[1]
            elif '时间：' in text and '获得魔力值：' in text:
                checkin_time = text.split('时间：')[1].split('获得魔力值：')[0].strip()
                magic_points = int(text.split('获得魔力值：')[1].split('）')[0].strip().replace(' ', ''))
                checkin_records.append({'time': checkin_time, 'magic_points': magic_points})

        # 打印提取的信息
        print(f"用户名: {user_name}")
        print(f"用户ID: {user_id}")
        print(f"总签到天数: {total_days}")
        print(f"连续签到天数: {consecutive_days}")
        print(f"第一次签到: {first_checkin}")
        print(f"距今: {days_since_first_checkin}")
        print(f"本次连续签到开始时间: {current_consecutive_start}")
        print("签到记录:")
        for record in checkin_records:
            print(f"  时间: {record['time']}, 魔力值: {record['magic_points']}")


if __name__ == '__main__':
    unittest.main()
