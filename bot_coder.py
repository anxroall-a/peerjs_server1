import os, requests, telebot, zipfile, io
from flask import Flask

# 1. PASTE YOUR KEYS HERE
TELEGRAM_TOKEN = "8757397280:AAFxnPPdQbaMaXSOywvenslfEsC5pCg_L1E"
NVIDIA_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
IMG_URL = "https://integrate.api.nvidia.com/v1/generate/images"

def generate_full_code(prompt):
    system = """You are a senior programmer. Write FULL, WORKING, production-ready code.
    Rules:
    1. No placeholders like '# add code here'. Write everything.
    2. If multiple files are needed, use this format:
       ---FILE: main.py---
       code here
       ---FILE: requirements.txt---
       code here
    3. Add comments. No errors."""

    data = {
        "model": "meta/llama-3.3-70b-instruct",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Task: {prompt}"}
        ],
        "max_tokens": 16384,
        "temperature": 0.2
    }
    r = requests.post(NVIDIA_URL, headers={"Authorization":f"Bearer {NVIDIA_KEY}"}, json=data)
    return r.json()["choices"][0]["message"]["content"]

def send_as_zip(chat_id, code_text, prompt):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

        # Split into multiple files if AI used ---FILE: ---
        parts = code_text.split("---FILE:")
        if len(parts) > 1:
            for part in parts[1:]:
                filename, filecode = part.split("---", 1)
                filename = filename.strip()
                filecode = filecode.strip()
                zip_file.writestr(filename, filecode)
        else:
            # Single file
            zip_file.writestr("main.py", code_text)

    zip_buffer.seek(0)
    bot.send_document(chat_id, zip_buffer, caption=f"Project: {prompt}")

@bot.message_handler(commands=['code'])
def handle_code(message):
    prompt = message.text.replace("/code ","")
    if not prompt:
        bot.reply_to(message, "Usage: /code build me a website")
        return

    bot.reply_to(message, "Vibe coding... this may take 30-60s for big projects ⏳")

    try:
        full_code = generate_full_code(prompt)
        send_as_zip(message.chat.id, full_code, prompt)
        bot.send_message(message.chat.id, "Done ✅ \nWant preview image? Use /img describe your app")

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['img'])
def handle_img(message):
    prompt = message.text.replace("/img ","")
    bot.reply_to(message, "Generating image...")
    data = {"model":"stabilityai/stable-diffusion-xl", "prompt": prompt + ", UI mockup, clean, app screenshot"}
    r = requests.post(IMG_URL, headers={"Authorization":f"Bearer {NVIDIA_KEY}"}, json=data)
    url = r.json()["data"][0]["url"]
    bot.send_photo(message.chat.id, url, caption=prompt)

@app.route("/")
def home(): return "Vibe Coder Bot Alive"

import threading
def run_bot(): bot.polling(none_stop=True)
threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)