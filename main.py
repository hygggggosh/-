#!/usr/bin/env python3
"""
Hermes Chat — KivyMD本地对话框架
APK打包版，访问 http://127.0.0.1:8084
"""
import json
import threading
import requests
from datetime import datetime

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.chip import MDChip
from kivymd.uix.snackbar import Snackbar

# ── 配置 ───────────────────────────────────────────
HERMES_API = "http://127.0.0.1:8642"
API_KEY    = "VI7IxKay3liyWc76H7g43iFT8xWvg2MZD2S49-bp8uQ"
PORT       = 8084

KV = """
<ChatBubble@MDBoxLayout>:
    orientation: "vertical"
    size_hint: None, None
    width: "320dp"
    padding: "8dp"
    radius: "12dp"

<MyScroll@MDScrollView>:
    size_hint: 1, 1

BoxLayout:
    orientation: "vertical"
    spacing: "8dp"
    padding: "8dp"

    # 顶栏
    MDBoxLayout:
        size_hint_y: None
        height: "48dp"
        padding: "8dp"
        md_bg_color: [0.05, 0.05, 0.1, 1]

        MDLabel:
            text: "⚡ Hermes Chat"
            font_size: "18sp"
            bold: True
            color: [1, 0.84, 0, 1]

        MDChip:
            text: "hermes-agent"
            chip_color: [1, 0.84, 0, 0.2]
            text_color: [1, 0.84, 0, 1]
            label_color: [1, 0.84, 0, 1]
            icon: ""
            size_hint_x: None
            width: "120dp"

    # 对话区
    MyScroll:
        id: scroll

        MDGridLayout:
            id: chat_area
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            padding: "8dp"
            spacing: "8dp"

    # 输入区
    MDBoxLayout:
        size_hint_y: None
        height: "56dp"
        spacing: "8dp"
        padding: "4dp"

        MDTextField:
            id: msg_input
            mode: "outlined"
            hint_text: "输入消息..."
            multiline: False
            on_text_validate: app.send_message()

        MDRaisedButton:
            text: "发送"
            on_release: app.send_message()
            md_bg_color: [1, 0.84, 0, 1]
            text_color: [0, 0, 0, 1]

    # 状态栏
    MDBoxLayout:
        size_hint_y: None
        height: "32dp"
        spacing: "16dp"
        padding: "4dp"

        MDLabel:
            id: status_label
            text: "就绪"
            font_size: "12sp"
            color: [0.5, 0.5, 0.5, 1]

        MDLabel:
            id: token_label
            text: "In: 0  Out: 0"
            font_size: "12sp"
            color: [0.5, 0.5, 0.5, 1]
"""


class HermesApp(MDApp):
    def build(self):
        self.chat_area = None
        self.msg_input = None
        self.status_label = None
        self.token_label = None
        self.thread = None
        self.messages = []
        return Builder.load_string(KV)

    def on_start(self):
        self.msg_input = self.root.ids.msg_input
        self.chat_area = self.root.ids.chat_area
        self.status_label = self.root.ids.status_label
        self.token_label = self.root.ids.token_label
        self.msg_input.focus = True

        label = MDLabel(
            text="发送消息开始对话...",
            halign="center",
            color=[0.4, 0.4, 0.4, 1],
            font_size="14sp"
        )
        self.chat_area.add_widget(label)

    def add_bubble(self, role, content, tokens_in=0, tokens_out=0):
        is_user = role == "user"
        bg = [1, 0.84, 0, 0.15] if is_user else [0.2, 0.2, 0.25, 1]
        txt_color = [0, 0, 0, 1] if is_user else [0.9, 0.9, 0.9, 1]
        label_color = [1, 0.84, 0, 1] if is_user else [0.3, 0.9, 0.5, 1]

        bubble = MDBoxLayout(
            orientation="vertical",
            size_hint_x=None,
            width="300dp",
            padding=("8dp", "6dp", "8dp", "6dp"),
            radius="12dp",
            md_bg_color=bg,
        )
        lbl = MDLabel(
            text="ME" if is_user else "AI",
            font_size="10sp",
            bold=True,
            color=label_color,
            size_hint_y=None,
            height="18dp"
        )
        msg = MDLabel(
            text=content,
            font_size="14sp",
            color=txt_color,
            text_size=("280dp", None),
            valign="top"
        )

        if is_user:
            bubble.add_widget(msg)
            bubble.add_widget(lbl)
        else:
            bubble.add_widget(lbl)
            bubble.add_widget(msg)

        if self.chat_area.children and isinstance(self.chat_area.children[0], MDLabel):
            self.chat_area.remove_widget(self.chat_area.children[0])

        self.chat_area.add_widget(bubble)

        if tokens_in or tokens_out:
            self.token_label.text = f"In: {tokens_in}  Out: {tokens_out}"

        Clock.schedule_once(lambda dt: self._scroll_down(), 0.1)

    def _scroll_down(self):
        scroll = self.root.ids.scroll
        scroll.scroll_to(self.chat_area)

    def set_status(self, text, color=None):
        self.status_label.text = text

    def send_message(self):
        text = self.msg_input.text.strip()
        if not text:
            return

        self.msg_input.text = ""
        self.set_status("思考中...", [1, 0.84, 0, 1])

        self.add_bubble("user", text)

        self.thread = threading.Thread(target=self._fetch_reply, args=(text,))
        self.thread.start()

    def _fetch_reply(self, text):
        try:
            resp = requests.post(
                f"{HERMES_API}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "hermes-agent",
                    "messages": [{"role": "user", "content": text}],
                    "stream": False,
                },
                timeout=60
            )
            data = resp.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "(无输出)")
            usage = data.get("usage", {})
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)

            Clock.schedule_once(lambda dt: self.add_bubble(
                "assistant", reply, tokens_in, tokens_out
            ))
            Clock.schedule_once(lambda dt: self.set_status("就绪", [0.3, 0.9, 0.5, 1]))

        except Exception as e:
            Clock.schedule_once(lambda dt: self.add_bubble(
                "assistant", f"Error: {str(e)}"
            ))
            Clock.schedule_once(lambda dt: self.set_status("错误", [1, 0.3, 0.3, 1]))


if __name__ == "__main__":
    from kivy.base import Clock
    HermesApp().run()