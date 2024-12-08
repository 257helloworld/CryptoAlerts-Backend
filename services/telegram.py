import pyrogram
import pyrogram.errors
import json
import key as tk
from templates import alert_telegram

api_id = tk.telegram_app_api_id
api_hash = tk.telegram_app_api_hash
bot_token = tk.telegram_bot_token

telegram_app = pyrogram.Client("cryptoalerts", api_id, api_hash, bot_token = bot_token)

@telegram_app.on_message(pyrogram.filters.command("verify"))
def verify_user(client, message):
    print('requested')
    with open("data/telegram_chat_ids.json", "r+") as f:
        isVerified = False
        f.seek(0)
        data = json.load(f)
        # print(message)
        for item in data:
            if item.get("username") == message.chat.username:
                isVerified = True

    if(isVerified):
        telegram_app.send_message(chat_id = message.chat.id, text = "✅ You are already verified!")
    else:
        newVerification = {'username': message.chat.username, 'chat_id': message.chat.id}
        data.append(newVerification)
        with open("data/telegram_chat_ids.json", "w+") as f:
            f.write(json.dumps(data, indent = 4))
        telegram_app.send_message(chat_id = message.chat.id, text = "🎉 You are now verified!\n\nSet alerts for your favourite crypto-currencies on [Crypto Alerts](https://google.com).", disable_web_page_preview= True)

@telegram_app.on_message(pyrogram.filters.command("send"))
def send_alert(client, message):
    message = alert_telegram.get_template()
    telegram_app.send_message(chat_id = 1132216525, text = message)