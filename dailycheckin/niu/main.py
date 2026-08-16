import base64
import json
import os
import time

import requests

from dailycheckin import CheckIn


class Niu(CheckIn):
    name = "小牛电动社区分享"

    APP_ID = "niu_ktdrr960"
    UA = (
        "manager/5.17.4 (android; ONEPLUS A5010 10);lang=zh-CN;"
        "clientIdentifier=Domestic;timezone=Asia/Shanghai;model=OnePlus_ONEPLUS A5010;"
        "deviceName=ONEPLUS A5010;ostype=android"
    )
    API_BASE = "https://app-api.niu.com"
    AUTH_URL = "https://account.niu.com/v3/api/oauth2/token"
    # token / 已分享帖子 id 持久化文件（建议加入 .gitignore）
    STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "niu_token.json")

    def __init__(self, check_item):
        self.check_item = check_item
        self.account = check_item.get("account", "")
        self.password = check_item.get("password", "")  # 密码 MD5（抓包得到）
        self.app_id = check_item.get("app_id", self.APP_ID)
        self.session = requests.session()
        self.session.headers.update({"user-agent": self.UA})

    # ---------- 基础工具 ----------
    @staticmethod
    def _jwt_exp(token):
        try:
            p = token.split(".")[1]
            p += "=" * (-len(p) % 4)
            return json.loads(base64.urlsafe_b64decode(p))["exp"]
        except Exception:
            return 0

    def _load_state(self):
        if os.path.exists(self.STATE_FILE):
            with open(self.STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        return data.get(self.account, {})

    def _save_state(self, state):
        all_state = {}
        if os.path.exists(self.STATE_FILE):
            with open(self.STATE_FILE, encoding="utf-8") as f:
                all_state = json.load(f)
        all_state[self.account] = state
        with open(self.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(all_state, f, ensure_ascii=False, indent=2)

    # ---------- 登录 / 刷新 ----------
    def _oauth(self, params):
        resp = self.session.post(
            self.AUTH_URL,
            data=params,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "token": "tokenExperienceMode",
                "x-no-encrypt": "1",
            },
            timeout=30,
        )
        return resp.json()

    def _login(self):
        data = self._oauth(
            {
                "password": self.password,
                "grant_type": "password",
                "scope": "base",
                "app_id": self.app_id,
                "account": self.account,
            }
        )
        if data.get("status") != 0:
            raise RuntimeError(f"登录失败: {data}")
        return data["data"]["token"]

    def _refresh(self, refresh_token):
        data = self._oauth(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "app_id": self.app_id,
                "scope": "base",
            }
        )
        if data.get("status") != 0:
            raise RuntimeError(f"刷新失败: {data}")
        return data["data"]["token"]

    def _ensure_token(self, state):
        now = int(time.time())
        access_token = state.get("access_token")
        refresh_token = state.get("refresh_token")

        if access_token and self._jwt_exp(access_token) > now + 86400:
            return access_token

        if refresh_token:
            try:
                tok = self._refresh(refresh_token)
                state["access_token"] = tok["access_token"]
                state["refresh_token"] = tok.get("refresh_token", refresh_token)
                state["access_exp"] = tok.get("token_expires_in")
                self._save_state(state)
                return state["access_token"]
            except Exception as e:
                print(f"[niu] refresh_token 刷新失败: {e}")

        tok = self._login()
        state["access_token"] = tok["access_token"]
        state["refresh_token"] = tok["refresh_token"]
        state["access_exp"] = tok.get("token_expires_in")
        self._save_state(state)
        return state["access_token"]

    # ---------- 社区分享 ----------
    def _get_posts(self, access_token):
        resp = self.session.get(
            f"{self.API_BASE}/community/api/posts/recommend/list",
            params={
                "page": 1,
                "version": 0,
                "page_size": 20,
                "_": int(time.time() * 1000),
            },
            headers={"token": access_token, "content-type": "application/json"},
            timeout=30,
        )
        return resp.json().get("data", {}).get("items", [])

    def _share(self, access_token, pid):
        resp = self.session.post(
            f"{self.API_BASE}/community/api/posts/shares",
            json={"id": pid},
            headers={
                "token": access_token,
                "content-type": "application/json; charset=utf-8",
            },
            timeout=30,
        )
        return resp.json()

    def _points(self, access_token):
        resp = self.session.get(
            f"{self.API_BASE}/v5/points/index",
            headers={"token": access_token, "content-type": "application/json"},
            timeout=30,
        )
        return resp.json().get("data", {}).get("userPoints")

    def main(self):
        state = self._load_state()
        access_token = self._ensure_token(state)

        items = self._get_posts(access_token)
        if not items:
            return "获取帖子列表失败"

        shared = set(state.get("shared", []))
        target = next((it for it in items if it["id"] not in shared), items[0])
        pid = target["id"]

        result = self._share(access_token, pid)
        msg = [f"账号: {self.account}", f"分享帖子: {pid}"]
        if result.get("status") == 0:
            shared.add(pid)
            state["shared"] = list(shared)
            self._save_state(state)
            msg.append("分享结果: 成功")
        else:
            msg.append(f"分享结果: 失败 {result}")

        try:
            points = self._points(access_token)
            if points is not None:
                msg.append(f"当前积分: {points}")
        except Exception:
            pass

        return "\n".join(msg)


if __name__ == "__main__":
    with open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json"),
        encoding="utf-8",
    ) as f:
        datas = json.loads(f.read())
    _check_item = datas.get("NIU", [])[0]
    print(Niu(check_item=_check_item).main())
