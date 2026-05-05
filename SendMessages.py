"""
Telegram Group Automation Tool - Bulk Messaging Tool

Author: VIP Bishnoi
GitHub: https://github.com/viphacke
Description: Script to send bulk messages to users from CSV.
License: MIT
"""

from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError
import sys
import csv
import random
import time

# --- Telegram API Credentials ---
api_id = 24509726
api_hash = 'a09cb4db3861dcbba941ba96620737d5'
phone = '+916378941259'

# --- Sleep Timings ---
SLEEP_TIME_2 = 0.5   # Flood error cooldown
SLEEP_TIME_1 = 0.5  # Generic error cooldown
SLEEP_TIME = 0.5       # Delay after each message

# --- CSV Path (must include file name + extension) ---
CSV_PATH = r"D:\MembersTG\Members\members.csv"

# --- Connect to Telegram ---
client = TelegramClient(phone, api_id, api_hash)
client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Enter the code: '))

# --- Read Users from CSV ---
users = []
with open(CSV_PATH, encoding='utf-8') as f:
    rows = csv.reader(f, delimiter=",", lineterminator="\n")
    next(rows, None)  # Skip header
    for row in rows:
        try:
            user = {
                'username': row[0],
                'id': int(row[1]),
                'access_hash': int(row[2]),
                'name': row[3]
            }
            users.append(user)
        except Exception as e:
            print(f"❌ Error reading row: {row} | {e}")
            continue

# --- Choose Mode ---
mode = int(input("Enter 1 to send by user ID or 2 to send by username: "))

# --- Messages List ---
messages = [
    """Hello {}, How are you? Did you join the latest trusted Telegram channel yet?\n\nIf not, join now 👉 💀 𝙑𝙄𝙋 = 𝙑𝙞𝙧𝙪𝙨 𝙄𝙣 𝙋𝙧𝙤𝙜𝙧𝙖𝙢 ⚠️ | 𝗥𝗼𝗼𝘁 𝗔𝗰𝗰𝗲𝘀𝘀 🔐

 𓆩 🔥 𝘛𝘩𝘦 𝘙𝘦𝘢𝘭 𝘎𝘢𝘮𝘦 𝘰𝘧 𝘋𝘢𝘳𝘬 𝘏𝘢𝘤𝘬𝘪𝘯𝘨 𝘉𝘦𝘨𝘪𝘯𝘴 𝘏𝘦𝘳𝘦... 🔥 𓆪 



━━━━━━━━━━━━━━━━━━━━━━
𓊈📂⛓️ 𝙑𝙄𝙋 𝙎𝙏𝘼𝘾𝙆 ⛓️📂𓊉
☠️ 𝘿𝙤𝙭𝙞𝙣𝙜
☠️ 𝙊𝙎𝙄𝙉𝙏
☠️ 𝙍𝘼𝙏 + 𝘾2
☠️ 𝙎𝙢𝙎 𝘽𝙤𝙢𝙗 | 𝙊𝙏𝙋 𝙃𝙞𝙩
☠️ 𝙒𝙝𝙖𝙩𝙨𝙖𝙥𝙥/𝙄𝙣𝙨𝙩𝙖 𝙋𝙖𝙮/𝘽𝙤𝙩
☠️ 𝘿𝙖𝙧𝙠 𝙒𝙚𝙗 | 𝙁𝙁 𝙃𝙖𝙘𝙠𝙨
━━━━━━━━━━━━━━━━━━━━━━

🛡️ 𝙊𝙒𝙉𝙀𝙍 : @VIPBHAI0029
👁️‍🗨️ 𝘾𝙊-𝙁𝙊𝙐𝙉𝘿𝙀𝙍 : @TheD4X
⚠️𝘿𝙈 𝙂𝘼𝙏𝙀𝙒𝘼𝙔 :@Dmvipd4xbot

━━━━━━━━━━━━━━━━━━━━━━

📡 𝙎𝙀𝘾𝙍𝙀𝙏 𝙇𝘼𝘽:
🔗 𝙑𝙄𝙋 𝘾𝙊𝙍𝙀 →
 https://t.me/+2CLc_2_GLRY4ZjM1

🔗 𝘿𝟜𝙓 𝘾𝙊𝙍𝙀 →
 https://t.me/+datSG_dhanwzMmVl"""
]

# --- Send Messages ---
for user in users:
    try:
        if mode == 2:  # By username
            if not user['username']:
                continue
            receiver = client.get_input_entity(user['username'])
        elif mode == 1:  # By ID
            receiver = InputPeerUser(user['id'], user['access_hash'])
        else:
            print("❌ Invalid Mode. Exiting.")
            client.disconnect()
            sys.exit()

        message = random.choice(messages)
        print(f"📩 Sending message to: {user['name']}")
        client.send_message(receiver, message.format(user['name']))
        print(f"⏳ Waiting {SLEEP_TIME} seconds...")
        time.sleep(SLEEP_TIME)

    except PeerFloodError:
        print("⚠️ Flood Error: Stopping now. Try again later.")
        print(f"⏳ Waiting {SLEEP_TIME_2} seconds...")
        time.sleep(SLEEP_TIME_2)
        break  # Stop script completely to avoid ban
    except Exception as e:
        print(f"❌ Error with {user['name']}: {e}")
        print(f"⏳ Waiting {SLEEP_TIME_1} seconds before continuing...")
        time.sleep(SLEEP_TIME_1)
        continue

client.disconnect()
print("✅ Done. Messages sent to available users.")
