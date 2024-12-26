
import requests
import os
import json

from dailycheckin import CheckIn

class PTTime(CheckIn):
    name = "PTTime"

    def __init__(self, check_item: dict):
        self.check_item = check_item

    def sign(self, headers, uid):
        url = "https://www.pttime.org/attendance.php?type=sign&uid={uid}"
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return f"签到失败，状态码: {response.status_code}"

    def main(self):
        cookie = self.check_item.get("cookie")
        uid = self.check_item.get("uid")
        headers = {
            "Host": "www.pttime.org",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": cookie,
            "Priority": "u=0, i",
            "Referer": "https://www.pttime.org/",
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        sign_result = self.sign(headers, uid)
        msg = f"签到结果: {sign_result}"
        return msg


if __name__ == "__main__":
    with open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json"),
        encoding="utf-8",
    ) as f:
        datas = json.loads(f.read())
    _check_item = datas.get("PTTime", [])[0]
    print(PTTime(check_item=_check_item).main())