import telebot
import config
import json
import requests
import io

from telebot import types, logging
from telebot import TeleBot
from fastapi import FastAPI, Request, BackgroundTasks

telebot.telebot.logger.setLevel(logging.INFO)

bot = TeleBot(config.tg_token)
app = FastAPI()

def download_file_from_max(file_id):
    url = f"{config.max_api_url}/getFile"
    headers = {"Authorization": f"Bearer {config.max_token}"}
    response = requests.get(url, headers=headers, params={"file_id": file_id}).json()

    file_path = response.get("result", {}).get("file_path")
    download_url = f"{config.max_api_url}/file/{file_path}"
    file_data = requests.get(download_url, headers=headers)

    return io.BytesIO(file_data.content)

def process_messages(update: dict):
    message = update.get("message", {})
    user = message.get("from", {}).get("name", "Аноним")
    caption = message.get("caption", "")

    if "text" in message:
        forward_text = f"🗣 *{user}* (MAX):\n{message['text']}"
        bot.send_message(chat_id=config.chat_id, text=forward_text, parse_mode='Markdown')
    elif "photo" in message:
        process_file("photo", user, caption, message)
    elif "video" in message:
        process_file("video", user, caption, message)
    elif "voice" in message:
        process_file("voice", user, caption, message)
    elif "document" in message:
        process_file("document", user, caption, message)


def process_file(file_type, user, caption, message):
    data = message[file_type]
    file_info = data[-1] if isinstance(data, list) else data
    file_id = file_info["file_id"]
    file = download_file_from_max(file_id)

    if file:
        message_caption = f"🗣 *{user}* (MAX):"
        if caption:
            message_caption += f"\n{caption}"

        match file_type:
            case "photo":
                bot.send_photo(chat_id=config.chat_id, photo=file, caption=message_caption, parse_mode="Markdown")
            case "video":
                bot.send_video(chat_id=config.chat_id, video=file, caption=message_caption, parse_mode="Markdown")
            case "voice":
                bot.send_audio(chat_id=config.chat_id, audio=file, caption=message_caption, parse_mode="Markdown")
            case "document":
                bot.send_document(chat_id=config.chat_id, document=file, caption=message_caption, parse_mode="Markdown")

@app.post("/max-webhook")
async def get_max_updates(request: Request, background_tasks: BackgroundTasks):
    update = await request.json()

    print("ПОЛУЧЕН ВЕБХУК ОТ MAX:", update, flush=True)

    background_tasks.add_task(process_messages, update)

    return {"status": "ok"}