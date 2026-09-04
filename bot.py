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

def process_messages(update: dict):
    message = update.get("message", {})
    body = message.get("body", {})
    sender = message.get("sender", {})

    user = sender.get("name", sender.get("first_name", "Аноним"))
    caption = body.get("text", "")

    attachments = body.get("attachments", [])

    if attachments:
        for attachment in attachments:
            file_type = attachment.get("type")
            payload = attachment.get("payload", {})
            file_name = attachment.get("filename", "document.file")

            file_url = payload.get("url")

            if file_url:
                process_file(file_type, user, caption, file_url, file_name)

    elif caption:
        forward_text = f"🗣 *{user}* (MAX):\n{caption}"
        bot.send_message(chat_id=config.chat_id, text=forward_text, parse_mode='Markdown')


def process_file(file_type, user, caption, file_url, file_name):
    response = requests.get(file_url)

    file = io.BytesIO(response.content)
    file.name = file_name

    message_caption = f"🗣 *{user}* (MAX):"
    if caption:
        message_caption += f"\n{caption}"

    match file_type:
        case "image":
            bot.send_photo(chat_id=config.chat_id, photo=file, caption=message_caption, parse_mode="Markdown", show_caption_above_media=True)
        case "video":
            bot.send_video(chat_id=config.chat_id, video=file, caption=message_caption, parse_mode="Markdown", show_caption_above_media=True)
        case "audio" | "voice":
            bot.send_audio(chat_id=config.chat_id, audio=file, caption=message_caption, parse_mode="Markdown")
        case _:
            bot.send_document(chat_id=config.chat_id, document=file, caption=message_caption, parse_mode="Markdown")

@app.post("/max-webhook")
async def get_max_updates(request: Request, background_tasks: BackgroundTasks):
    update = await request.json()
    message = update.get("message", {})
    chat_type = message.get("recipient", {}).get("chat_type", "")

    print("WEBHOOK WORKED", update, flush=True)

    if chat_type == "chat":
        background_tasks.add_task(process_messages, update)
    else:
        print(f"MESSAGE SENDED IN DIALOG: {message.get("body", {}).get("text", "")}")

    return {"status": "ok"}

@app.get("/")
async def ping():
    return {"status": "ok"}