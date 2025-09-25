from telethon import TelegramClient, events
import os
import time
import asyncio
import datetime
import sys

print("🚀 Starting Telegram Bot on Render.com...")

# Environment variables se API credentials lo
api_id = int(os.environ.get('API_ID', 0))
api_hash = os.environ.get('API_HASH', '')
phone_number = os.environ.get('PHONE_NUMBER', '')

print(f"🔧 API_ID: {'✅ Set' if api_id else '❌ Missing'}")
print(f"🔧 API_HASH: {'✅ Set' if api_hash else '❌ Missing'}")
print(f"🔧 PHONE_NUMBER: {'✅ Set' if phone_number else '❌ Missing'}")

if not api_id or not api_hash or not phone_number:
    print("❌ ERROR: Please set API_ID, API_HASH, and PHONE_NUMBER environment variables")
    sys.exit(1)

session_name = "my_account"

# Special Render settings - IMPORTANT!
client = TelegramClient(
    session_name, 
    api_id, 
    api_hash,
    connection_retries=10,  # Increase retries
    request_retries=10,     # Increase request retries
    auto_reconnect=True,    # Auto reconnect
    timeout=60,             # Increase timeout
    proxy=None              # No proxy
)

DM_REPLY = "𝘾𝙐𝙍𝙍𝙀𝙉𝙏𝙇𝙔 𝙊𝙁𝙁𝙇𝙄𝙉𝙀!🔕  𝙋𝙇𝙀𝘼𝙎𝙀 𝘿𝙍𝙊𝙋 𝙔𝙊𝙐𝙍 𝙈𝙀𝙎𝙎𝘼𝙂𝙀, 𝙒𝙄𝙇𝙇 𝙍𝙀𝙎𝙋𝙊𝙉𝘿 𝙏𝙊 𝙔𝙊𝙐 𝙇𝘼𝙏𝙀𝙍!💋"
GROUP_REPLY = "𝘾𝙐𝙍𝙍𝙀𝙉𝙏𝙇𝙔 𝙊𝙁𝙁𝙇𝙄𝙉𝙀, 𝙒𝙄𝙇𝙇 𝙍𝙀𝙋𝙇𝙔 𝙒𝙃𝙀𝙉 𝙄'𝙈 𝙊𝙉𝙇𝙄𝙉𝙀"

auto_reply_enabled = False
smart_mode_enabled = True
night_mode_enabled = True
people_memory = {}
owner_id = None
last_online_check = 0

async def connect_telegram():
    """Telegram se connect karta hai with retry logic"""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"🔗 Connection attempt {attempt + 1}/{max_retries}...")
            
            # Connect to Telegram
            await client.connect()
            print("✅ Connected to Telegram servers")
            
            # Check if already logged in
            if await client.is_user_authorized():
                print("✅ Already logged in")
                return True
            
            # Send code request
            print(f"📱 Sending code to: {phone_number}")
            await client.send_code_request(phone_number)
            print("✅ Code sent successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in 10 seconds...")
                await asyncio.sleep(10)
            else:
                print("❌ All connection attempts failed")
                return False

async def sign_in():
    """Sign in process handle karta hai"""
    verification_code = os.environ.get('VERIFICATION_CODE', '')
    two_fa_password = os.environ.get('TWO_FA_PASSWORD', '')
    
    if not verification_code:
        print("❌ VERIFICATION_CODE not set in environment variables")
        print("💡 After receiving code, add VERIFICATION_CODE and redeploy")
        return False
    
    try:
        print(f"🔑 Signing in with code: {verification_code}")
        await client.sign_in(phone_number, verification_code)
        print("✅ Signed in successfully!")
        
        # Handle 2FA if needed
        if two_fa_password:
            print("🔒 Signing in with 2FA...")
            await client.sign_in(password=two_fa_password)
            print("✅ 2FA sign in successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Sign in failed: {e}")
        return False

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
    print("🔗 Connecting to Telegram...")
    
    # Connect to Telegram
    if not await connect_telegram():
        print("❌ Failed to connect to Telegram")
        return
    
    # Sign in if needed
    if not await client.is_user_authorized():
        if not await sign_in():
            print("❌ Sign in failed")
            return
    
    await detect_owner()
    asyncio.create_task(smart_monitor())
    
    print("✅ Render.com Bot Started Successfully!")
    print("🤖 Smart Auto-Toggle Features Active!")
    print("🌐 Bot is running 24/7 on Render!")
    
    # Keep bot running
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Check Render logs for details")