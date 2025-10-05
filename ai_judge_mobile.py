#mobile device friendly
#!/usr/bin/env python3
# ai_judge_mobile.py
# Mobile-friendly version of AI Judge Game using Kivy


import random
import time
import os
from cryptography.fernet import Fernet
import ollama
from AI_Game import get_judge_verdict
from ollama_case_generator import get_case, generate_verdict_score
from serious_cases import SERIOUS_CASES
from casual_cases import CASUAL_CASES
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen

# === Encryption file names ===
COINS_FILE = "coins.dat"
KEY_FILE = "secret.key"

# === Encryption Key Handling ===
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

def load_key():
    if not os.path.exists(KEY_FILE):
        generate_key()
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

fernet = Fernet(load_key())

# === Save / Load coins with encryption ===
def save_coins_encrypted(coins: int):
    data = str(coins).encode()
    encrypted = fernet.encrypt(data)
    with open(COINS_FILE, "wb") as f:
        f.write(encrypted)

def load_coins_encrypted() -> int:
    if not os.path.exists(COINS_FILE):
        return 0
    with open(COINS_FILE, "rb") as f:
        encrypted = f.read()
    try:
        decrypted = fernet.decrypt(encrypted)
        return int(decrypted.decode())
    except Exception:
        return 0

# === Kivy App Screens ===
class StartScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        background = Image(source="main_menu_bg.png", allow_stretch=True, keep_ratio=False)
        start_button = Button(background_normal="/mnt/data/A_2D_digital_graphic_features_a_rectangular_button.png", size_hint=(0.5, 0.2), pos_hint={"center_x": 0.5})
        start_button.bind(on_press=self.start_game)
        layout.add_widget(background)
        layout.add_widget(start_button)
        self.add_widget(layout)

    def start_game(self, instance):
        self.manager.current = "mode"

class ModeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=10)
        modes = ["Casual", "Serious", "AI Casual", "AI Serious"]
        for mode in modes:
            btn = Button(text=mode)
            btn.bind(on_press=self.select_mode)
            layout.add_widget(btn)
        self.add_widget(layout)

    def select_mode(self, instance):
        self.manager.mode = instance.text.lower().replace(" ", "-")
        self.manager.current = "game"

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.judge_image = Image(source="judge.png", size_hint=(1, 0.5))
        self.case_label = Label(text="", size_hint=(1, 0.3), font_size=16)
        self.defense_input = TextInput(hint_text="Enter your defense", multiline=False)
        self.submit_button = Button(text="Submit Defense")
        self.submit_button.bind(on_press=self.submit_defense)
        self.result_label = Label(text="")

        self.layout.add_widget(self.judge_image)
        self.layout.add_widget(self.case_label)
        self.layout.add_widget(self.defense_input)
        self.layout.add_widget(self.submit_button)
        self.layout.add_widget(self.result_label)
        self.add_widget(self.layout)

    def on_enter(self):
        self.case = get_case(self.manager.mode, "normal")
        self.case_label.text = f"👨‍⚖️ Judge says: {self.case}"
        self.result_label.text = ""
        self.defense_input.text = ""

    def submit_defense(self, instance):
        defense = self.defense_input.text.strip()
        if not defense:
            self.result_label.text = "Please enter a defense."
            return
        score, explanation = generate_verdict_score(defense, self.case)
        verdict = get_judge_verdict(self.case, defense)
        result = f"Score: {score}/100\n{explanation}\nVerdict: {verdict}"
        self.result_label.text = result

class CourtApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartScreen(name="start"))
        sm.add_widget(ModeScreen(name="mode"))
        sm.add_widget(GameScreen(name="game"))
        sm.mode = "casual"
        return sm

if __name__ == "__main__":
    CourtApp().run()
