import random
import re
import ollama
from serious_cases import SERIOUS_CASES
from casual_cases import CASUAL_CASES

def trim_text(text: str, max_sentences: int = 3) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return ' '.join(sentences[:max_sentences]).strip()

def generate_case_with_ollama(difficulty: str) -> str:
    prompt = f"""
Create a {difficulty} legal case for a courtroom video game.

The case should be short and under 5 sentences. Do not include legal jargon.
Return only the case description, no extra commentary.
"""
    response = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": "You are a creative legal writer."},
            {"role": "user", "content": prompt},
        ],
        options={
            "temperature": 0.7,
            "num_predict": 60,
        },
        stream=True
    )

    full_text = ""
    for chunk in response:
        if "message" in chunk and "content" in chunk["message"]:
            full_text += chunk["message"]["content"]
    return full_text.strip()

def get_case(mode: str = "casual", difficulty: str = "normal") -> str:
    if mode == "ollama-casual":
        case = generate_case_with_ollama("casual")
    elif mode == "ollama-serious":
        case = generate_case_with_ollama("serious")
    elif mode == "serious":
        case = random.choice(SERIOUS_CASES)
    elif mode == "casual":
        case = random.choice(CASUAL_CASES)
    else:
        print("Unknown mode. Falling back to casual.")
        case = random.choice(CASUAL_CASES)

    return trim_text(case, 3)

def generate_verdict_score(defense_text: str, case_text: str) -> tuple:
    prompt = f"""
You are a fair and concise courtroom judge. Read the legal case and the player's defense, then score the defense.

Case: {case_text}
Defense: {defense_text}

Score the defense from 0 (terrible) to 100 (perfect). Respond ONLY with:
- Score (0–100)
- A one-sentence explanation
Format: SCORE: <number> | EXPLANATION: <short explanation>
"""
    response = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": "You are an AI courtroom judge."},
            {"role": "user", "content": prompt}
        ],
        options={
            "temperature": 0.5,
            "num_predict": 60
        },
        stream=True
    )

    full_reply = ""
    for chunk in response:
        if "message" in chunk and "content" in chunk["message"]:
            full_reply += chunk["message"]["content"]

    match = re.search(r"SCORE:\s*(\d+)\s*\|\s*EXPLANATION:\s*(.*)", full_reply, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        explanation = match.group(2).strip()
        return score, explanation
    else:
        return 50, "Response could not be interpreted, default score applied."
