from telethon import TelegramClient, events
import os
import time
import asyncio
import datetime

api_id = int(os.environ.get('API_ID'))
api_hash = os.environ.get('API_HASH')
session_name = "my_account"

DM_REPLY = "𝘾𝙐𝙍𝙍𝙀𝙉𝙏𝙇𝙔 𝙊𝙁𝙁𝙇𝙄𝙉𝙀!🔕  𝙋𝙇𝙀𝘼𝙎𝙀 𝘿𝙍𝙊𝙋 𝙔𝙊𝙐𝙍 𝙈𝙀𝙎𝙎𝘼𝙂𝙀, 𝙒𝙄𝙇𝙇 𝙍𝙀𝙎𝙋𝙊𝙉𝘿 𝙏𝙊 𝙔𝙊𝙐 𝙇𝘼𝙏𝙀𝙍!💋"
GROUP_REPLY = "𝘾𝙐𝙍𝙍𝙀𝙉𝙏𝙇𝙔 𝙊𝙁𝙁𝙇𝙄𝙉𝙀, 𝙒𝙄𝙇𝙇 𝙍𝙀𝙋𝙇𝙔 𝙒𝙃𝙀𝙉 𝙄'𝙈 𝙊𝙉𝙇𝙄𝙉𝙀"

auto_reply_enabled = False
smart_mode_enabled = True
night_mode_enabled = True
people_memory = {}
owner_id = None
last_online_check = 0

client = TelegramClient(session_name, api_id, api_hash)

async def detect_owner():
    global owner_id
    me = await client.get_me()
    owner_id = me.id
    print(f"👤 Owner ID detected: {owner_id}")
    return owner_id

async def delete_after_delay(message, delay=10):
    await asyncio.sleep(delay)
    try:
        await message.delete()
        print(f"🗑️ Message deleted after {delay} seconds")
    except Exception as e:
        print(f"❌ Could not delete message: {e}")

async def is_owner_online():
    global last_online_check
    if time.time() - last_online_check < 120:
        return None
    last_online_check = time.time()
    try:
        me = await client.get_me()
        user_full = await client.get_entity(me.id)
        if hasattr(user_full, 'status'):
            if user_full.status:
                if hasattr(user_full.status, 'was_online'):
                    time_since_online = time.time() - user_full.status.was_online.timestamp()
                    return time_since_online < 180
        return False
    except Exception as e:
        print(f"❌ Online check error: {e}")
        return None

def is_night_time():
    now = datetime.datetime.now().time()
    night_start = datetime.time(22, 0)
    night_end = datetime.time(8, 0)
    if now >= night_start or now <= night_end:
        return True
    return False

async def smart_toggle_check():
    global auto_reply_enabled, smart_mode_enabled, night_mode_enabled
    if not smart_mode_enabled:
        return
    if night_mode_enabled and is_night_time():
        if not auto_reply_enabled:
            auto_reply_enabled = True
            print("🌙 Night mode: Auto-reply turned ON")
        return
    is_online = await is_owner_online()
    if is_online is not None:
        if is_online:
            if auto_reply_enabled:
                auto_reply_enabled = False
                print("🟢 Owner online: Auto-reply turned OFF")
        else:
            if not auto_reply_enabled:
                auto_reply_enabled = True
                print("🔴 Owner offline: Auto-reply turned ON")

async def smart_monitor():
    while True:
        await smart_toggle_check()
        await asyncio.sleep(300)

@client.on(events.NewMessage(pattern='/mode'))
async def toggle_auto_reply(event):
    global auto_reply_enabled, smart_mode_enabled
    if event.sender_id == owner_id:
        auto_reply_enabled = not auto_reply_enabled
        smart_mode_enabled = False
        status = "ON 🟢" if auto_reply_enabled else "OFF 🔴"
        mode_type = "MANUAL 🔧"
        reply_msg = await event.reply(f"🤖 Auto-Reply: {status}\n📱 Mode: {mode_type}\n\n✅ Auto-delete in 10 seconds")
        asyncio.create_task(delete_after_delay(event.message))
        asyncio.create_task(delete_after_delay(reply_msg))
    else:
        reply_msg = await event.reply("❌ Only the owner can use this command.")
        asyncio.create_task(delete_after_delay(reply_msg))

@client.on(events.NewMessage(pattern='/smart'))
async def toggle_smart_mode(event):
    global smart_mode_enabled, night_mode_enabled
    if event.sender_id == owner_id:
        smart_mode_enabled = not smart_mode_enabled
        night_mode_enabled = smart_mode_enabled
        status = "ON 🟢" if smart_mode_enabled else "OFF 🔴"
        night_status = "ON 🌙" if night_mode_enabled else "OFF ☀️"
        reply_msg = await event.reply(f"🤖 Smart Mode: {status}\n🌙 Night Mode: {night_status}\n\n✅ Auto-delete in 10 seconds")
        asyncio.create_task(delete_after_delay(event.message))
        asyncio.create_task(delete_after_delay(reply_msg))

@client.on(events.NewMessage(pattern='/status'))
async def show_status(event):
    if event.sender_id == owner_id:
        status = "ON 🟢" if auto_reply_enabled else "OFF 🔴"
        smart_status = "ON 🟢" if smart_mode_enabled else "OFF 🔴"
        night_status = "ON 🌙" if night_mode_enabled else "OFF ☀️"
        now = datetime.datetime.now()
        is_night = is_night_time()
        night_info = "ACTIVE" if is_night else "INACTIVE"
        online_status = await is_owner_online()
        online_info = "ONLINE 🟢" if online_status else "OFFLINE 🔴"
        reply_msg = await event.reply(f"📊 Bot Status:\n\n🔧 Auto-Reply: {status}\n🤖 Smart Mode: {smart_status}\n🌙 Night Mode: {night_status}\n👤 Your Status: {online_info}\n🌙 Night Mode: {night_info}\n⏰ Time: {now.strftime('%I:%M %p')}")
        asyncio.create_task(delete_after_delay(event.message))
        asyncio.create_task(delete_after_delay(reply_msg))

@client.on(events.NewMessage(pattern='/help'))
async def show_help(event):
    if event.sender_id == owner_id:
        help_text = "🤖 Available Commands:\n\n/mode - Manual ON/OFF toggle\n/smart - Smart auto-toggle ON/OFF\n/status - Detailed status check\n/help - This help message\n\n✅ All messages auto-delete after 10 seconds"
        reply_msg = await event.reply(help_text)
        asyncio.create_task(delete_after_delay(event.message))
        asyncio.create_task(delete_after_delay(reply_msg))

@client.on(events.NewMessage(incoming=True))
async def auto_responder(event):
    if event.out: return
    if not auto_reply_enabled: return
    person_id = event.sender_id
    current_time = time.time()
    if person_id in people_memory:
        if current_time - people_memory[person_id] < 300: return
        del people_memory[person_id]
    if event.is_private:
        await event.reply(DM_REPLY)
        print(f"📩 Replied to DM from {person_id}")
    elif event.is_group:
        me = await client.get_me()
        should_reply = False
        if event.message.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg.sender_id == me.id: should_reply = True
        if not should_reply and event.message.entities:
            for entity in event.message.entities:
                if hasattr(entity, 'user_id'):
                    if entity.user_id == me.id:
                        should_reply = True
                        break
        if should_reply:
            await event.reply(GROUP_REPLY)
            print(f"👥 Replied to mention in group")
    people_memory[person_id] = current_time

async def main():
    await client.start()
    await detect_owner()
    asyncio.create_task(smart_monitor())
    print("✅ Render.com Bot Started Successfully!")
    print("🤖 Smart Auto-Toggle Features Active!")
    print("🌐 Bot is running 24/7 on Render!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())