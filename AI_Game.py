import random
import time
import os
from cryptography.fernet import Fernet
import ollama
from ollama_case_generator import get_case, generate_verdict_score
from serious_cases import SERIOUS_CASES
from casual_cases import CASUAL_CASES

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

# === Helper for slow typing effect ===
def slow_type(text: str, delay: float = 0.02):
    for c in text:
        print(c, end='', flush=True)
        time.sleep(delay)
    print()

# === Truncate long case text ===
def trim_text(text: str, max_sentences: int = 3) -> str:
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return ' '.join(sentences[:max_sentences])

# === Generate prompt for AI judge ===
def generate_prompt(case_text: str, defense_text: str) -> str:
    return f"""
You are a courtroom judge.
Case: {case_text}
Defense: \"{defense_text}\"
Respond with: guilty / not guilty / retrial and give a one-sentence explanation.
"""

# === Jail animation ===
def jail_animation():
    frames = [
        "[🟦🟦🟦🟦🟦]",
        "[🟦🚶‍♂️🟦🟦🟦]",
        "[🟦🟦🚶‍♂️🟦🟦]",
        "[🟦🟦🟦🚶‍♂️🟦]",
        "[🟦🟦🟦🟦🚶‍♂️]",
        "[🟦🟦🟦🟦🟦]",
    ]
    for _ in range(2):
        for frame in frames:
            print("\r" + frame, end="", flush=True)
            time.sleep(0.25)
    print("\nYou're in jail! Game over.")

# === Get verdict from Ollama AI with streaming ===
def get_judge_verdict(case: str, defense: str) -> str:
    prompt = generate_prompt(case, defense)
    stream = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": "You are an AI courtroom judge."},
            {"role": "user", "content": prompt},
        ],
        options={
            "temperature": 0.5,
            "num_predict": 60
        },
        stream=True
    )
    verdict = ""
    for chunk in stream:
        content = chunk['message']['content']
        print(content, end='', flush=True)
        verdict += content
    print()
    return verdict.strip().lower()

# === Game mode chooser ===
def choose_game_mode():
    print("Choose game mode:")
    print("1. Casual")
    print("2. Serious")
    print("3. AI Casual")
    print("4. AI Serious")
    mode_input = input("Enter choice: ")

    mode_map = {
        "1": "casual",
        "2": "serious",
        "3": "ollama-casual",
        "4": "ollama-serious"
    }

    return mode_map.get(mode_input, "casual")

# === Difficulty chooser ===
def choose_difficulty():
    print("\nChoose difficulty (this affects AI case complexity):")
    print("1. Easy")
    print("2. Normal")
    print("3. Hard")
    choice = input("Enter difficulty: ")

    difficulty_map = {
        "1": "easy",
        "2": "normal",
        "3": "hard"
    }

    return difficulty_map.get(choice, "normal")

# === Get lawyer hint from Ollama AI ===
def get_lawyer_hint(case: str) -> str:
    prompt = f"Provide a brief, simple hint to help defend this legal case:\n{case}"
    response = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": "You are a helpful lawyer giving advice."},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.6, "num_predict": 50}
    )
    return response["message"]["content"].strip()

# === Main gameplay loop ===
def play_mode(mode, difficulty):
    coins = load_coins_encrypted()
    slow_type(f"\n💰 Loaded coins: {coins}\n")

    while True:
        case = get_case(mode, difficulty)
        case = trim_text(case, 3)

        slow_type(f"\n👨‍⚖️ Judge: You are on trial. Case:\n{case}\n")

        if coins >= 100:
            buy_hint = input("Do you want to hire a lawyer for 100 coins to get a defense hint? (y/n): ").strip().lower()
            if buy_hint == 'y':
                coins -= 100
                hint = get_lawyer_hint(case)
                slow_type(f"\n🧑‍⚖️ Lawyer's hint: {hint}\n")
                save_coins_encrypted(coins)
                slow_type(f"Coins left: {coins}\n")

        defense = input("Your defense: ").strip()

        score, quality = generate_verdict_score(defense, case)
        slow_type(f"\n💡 Defense Score: {score}/100\n💭 Evaluation: {quality}\n")

        slow_type("\nJudge is considering your defense...\n")
        verdict_text = get_judge_verdict(case, defense)
        slow_type(f"\n👨‍⚖️ Judge's Verdict:\n{verdict_text}\n")

        if "not guilty" in verdict_text:
            coins += 10
            slow_type(f"🎉 Not guilty! You earned 10 coins. Total: {coins}\n")
        elif "guilty" in verdict_text and "not guilty" not in verdict_text:
            slow_type("You've been found guilty. You may appeal once.\n")
            appeal = input("Do you want to appeal? (y/n): ").strip().lower()
            if appeal == 'y':
                slow_type("🔁 Appeal submitted...\n")
                verdict_text = get_judge_verdict(case, defense + " (appeal)")
                slow_type(f"\nAppeal verdict:\n{verdict_text}\n")
            if "guilty" in verdict_text and "not guilty" not in verdict_text:
                jail_animation()
                break
            else:
                coins += 5
                slow_type(f"🎉 Appeal successful! +5 coins. Total: {coins}\n")
                save_coins_encrypted(coins)
        elif "retrial" in verdict_text:
            slow_type("Retrial granted. You may try a new defense.\n")
        else:
            slow_type("You're free. Case closed.\n")


        again = input("Defend another case? (y/n): ").strip().lower()
        if again != 'y':
            slow_type(f"\nCourt adjourned. Final coins: {coins}. Thanks for playing!\n")
            break

# === Main Entry Point ===
def main():
    slow_type("⚖️ Welcome to AI Judge: Courtroom Chaos ⚖️\n")
    mode = choose_game_mode()
    difficulty = choose_difficulty()
    play_mode(mode, difficulty)

if __name__ == "__main__":
    main()
