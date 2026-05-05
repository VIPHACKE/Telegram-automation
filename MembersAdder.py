# -*- coding: utf-8 -*-
"""
Telegram Group Automation Tool - Member Adder

Author: VIP Bishnoi
GitHub: https://github.com/viphacke
Description: Script to add members from CSV to a Telegram group.
License: MIT
"""

import os
import sys
import time
import glob
import random
import traceback
import pandas as pd

from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import (
    PeerFloodError,
    UserPrivacyRestrictedError,
)
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser

# -------------------- USER CONFIG --------------------
api_id = 24509726
api_hash = 'a09cb4db3861dcbba941ba96620737d5'
phone = '+916378941259'

INPUT_PATH = r"D:\MembersTG\Members"

SLEEP_BETWEEN_USERS_SEC = (1, 5)
SLEEP_BATCH_EVERY_N = 80
SLEEP_BATCH_SEC = 60
FLOOD_WAIT_COOLDOWN_SEC = 60
# ----------------------------------------------------


def log(msg: str):
    print(msg, flush=True)


def resolve_csv_files(path: str):
    if not os.path.exists(path):
        log(f"Error: Path '{path}' does not exist.")
        sys.exit(1)

    if os.path.isdir(path):
        csvs = sorted(glob.glob(os.path.join(path, "*.csv")))
        if not csvs:
            log(f"Error: No CSV files found in folder '{path}'.")
            sys.exit(1)
        return csvs
    else:
        if not path.lower().endswith(".csv"):
            log(f"Error: File '{path}' is not a .csv. Provide a CSV file.")
            sys.exit(1)
        return [path]


def read_users_from_csvs(csv_files):
    users = []
    wanted_cols = {
        "id": ["id", "user id", "user_id"],
        "username": ["username", "user name"],
        "access_hash": ["access_hash", "access hash"],
        "name": ["name", "full name"],
    }

    for csv_path in csv_files:
        log(f"Reading: {csv_path}")
        try:
            df = pd.read_csv(csv_path, dtype=str, encoding="utf-8", engine="python")
        except Exception as e:
            log(f"Error reading CSV '{csv_path}': {e}")
            continue

        df.columns = [str(c).strip().lower() for c in df.columns]

        def pick(col_aliases):
            for alias in col_aliases:
                if alias in df.columns:
                    return alias
            return None

        col_id = pick(wanted_cols["id"])
        col_un = pick(wanted_cols["username"])
        col_ah = pick(wanted_cols["access_hash"])
        col_nm = pick(wanted_cols["name"])

        if not (col_un or (col_id and col_ah)):
            log("Warning: Need either 'username' OR ('id' + 'access_hash') in CSV. Skipping this file.")
            continue

        for idx, row in df.iterrows():
            try:
                user = {"username": "", "id": 0, "access_hash": 0, "name": ""}
                if col_un and pd.notna(row.get(col_un, "")):
                    user["username"] = str(row[col_un]).strip().lstrip("@")
                if col_id and pd.notna(row.get(col_id, "")):
                    raw_id = str(row[col_id]).strip()
                    if raw_id.isdigit():
                        user["id"] = int(raw_id)
                if col_ah and pd.notna(row.get(col_ah, "")):
                    raw_ah = str(row[col_ah]).strip()
                    if raw_ah.replace("-", "").isdigit():
                        user["access_hash"] = int(raw_ah)
                if col_nm and pd.notna(row.get(col_nm, "")):
                    user["name"] = str(row[col_nm]).strip()
                if user["username"] or (user["id"] and user["access_hash"]):
                    users.append(user)
                else:
                    log(f"Skipping row {idx}: missing username and id/access_hash.")
            except Exception as e:
                log(f"Skipping invalid row {idx}: {e}")
                continue

    if not users:
        log("Error: No valid users found in provided CSVs.")
        sys.exit(1)

    return users


def connect_client():
    try:
        client = TelegramClient(phone, api_id, api_hash)
        client.connect()
        if not client.is_user_authorized():
            client.send_code_request(phone)
            code = input("Enter the code: ").strip()
            client.sign_in(phone, code)
        return client
    except Exception as e:
        log(f"Error connecting to Telegram: {e}")
        sys.exit(1)


def pick_target_group(client):
    try:
        result = client(GetDialogsRequest(
            offset_date=None,
            offset_id=0,
            offset_peer=InputPeerEmpty(),
            limit=200,
            hash=0
        ))
        chats = result.chats
    except Exception as e:
        log(f"Error fetching dialogs: {e}")
        sys.exit(1)

    groups = []
    for chat in chats:
        try:
            if getattr(chat, 'megagroup', False):
                groups.append(chat)
        except Exception:
            continue

    if not groups:
        log("No megagroups found.")
        sys.exit(1)

    log("Choose a group to add members:")
    for i, g in enumerate(groups):
        title = getattr(g, "title", "Unknown")
        log(f"{i} - {title}")

    try:
        g_index = int(input("Enter a Number: ").strip())
        target_group = groups[g_index]
        return target_group
    except (ValueError, IndexError):
        log("Invalid group selection.")
        sys.exit(1)


def add_users_to_group(client, users, target_group):
    try:
        target_group_entity = InputPeerChannel(target_group.id, target_group.access_hash)
    except Exception as e:
        log(f"Error accessing group: {e}")
        sys.exit(1)

    try:
        mode = int(input("Enter 1 to add by username or 2 to add by ID: ").strip())
        if mode not in (1, 2):
            raise ValueError
    except ValueError:
        log("Invalid Mode Selected. Please enter 1 or 2.")
        sys.exit(1)

    processed = 0
    for u in users:
        processed += 1
        if processed % SLEEP_BATCH_EVERY_N == 0:
            log(f"Processed {processed} users; cooling down for {SLEEP_BATCH_SEC} sec...")
            time.sleep(SLEEP_BATCH_SEC)

        try:
            if mode == 1:
                if not u["username"]:
                    log(f"Skipping user {u.get('id', '')}: Empty username.")
                    continue
                log(f"Adding by username: @{u['username']}")
                user_to_add = client.get_input_entity(u["username"])
            else:
                if not (u["id"] and u["access_hash"]):
                    log(f"Skipping user (missing id/access_hash).")
                    continue
                log(f"Adding by ID: {u['id']}")
                user_to_add = InputPeerUser(u["id"], u["access_hash"])

            client(InviteToChannelRequest(target_group_entity, [user_to_add]))
            log(f"✓ Added: {u.get('username') or u.get('id')}")
            time.sleep(random.randint(*SLEEP_BETWEEN_USERS_SEC))

        except PeerFloodError:
            log(f"⚠️ PeerFloodError: Cooling down {FLOOD_WAIT_COOLDOWN_SEC}s...")
            time.sleep(FLOOD_WAIT_COOLDOWN_SEC)
            continue
        except FloodWaitError as e:
            wait_for = getattr(e, "seconds", FLOOD_WAIT_COOLDOWN_SEC)
            log(f"⏳ FloodWaitError: Waiting {wait_for}s...")
            time.sleep(int(wait_for))
            continue
        except UserPrivacyRestrictedError:
            log("User privacy prevents adding. Skipping.")
            time.sleep(random.randint(*SLEEP_BETWEEN_USERS_SEC))
            continue
        except Exception as e:
            log(f"Unexpected error for user {u.get('id') or u.get('username')}: {e}")
            traceback.print_exc()
            time.sleep(1)
            continue

    log("Done adding users.")


def main():
    csv_files = resolve_csv_files(INPUT_PATH)
    log(f"Found {len(csv_files)} CSV file(s).")

    users = read_users_from_csvs(csv_files)
    log(f"Loaded {len(users)} user(s) from CSV.")

    client = connect_client()

    try:
        target_group = pick_target_group(client)
        add_users_to_group(client, users, target_group)
    finally:
        client.disconnect()
        log("Client disconnected.")


if __name__ == "__main__":
    main()
