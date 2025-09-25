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
phone_number = os.environ.get('PHONE_NUMBER', '')  # New: Phone number bhi environment variable se

# Debug information
print(f"🔧 API_ID: {'✅ Set' if api_id else '❌ Missing'}")
print(f"🔧 API_HASH: {'✅ Set' if api_hash else '❌ Missing'}")
print(f"🔧 PHONE_NUMBER: {'✅ Set' if phone_number else '❌ Missing'}")

if not api_id or not api_hash or not phone_number:
    print("❌ ERROR: Please set API_ID, API_HASH, and PHONE_NUMBER environment variables in Render.com")
    print("💡 Go to Render Dashboard → Your Service → Environment → Add variables")
    sys.exit(1)

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

async def send_code_request():
    """Phone number verification code send karta hai"""
    print(f"📱 Sending verification code to: {phone_number}")
    await client.send_code_request(phone_number)
    print("✅ Verification code sent to your Telegram app")

async def sign_in_with_code():
    """User se code input leke signin karta hai"""
    print("📝 Please check your Telegram app for verification code")
    
    # Render pe interactive input nahi le sakte, isliye environment variable use karenge
    verification_code = os.environ.get('VERIFICATION_CODE', '')
    
    if verification_code:
        print(f"🔑 Using verification code from environment: {verification_code}")
        try:
            await client.sign_in(phone_number, verification_code)
            print("✅ Signed in successfully with code!")
            return True
        except Exception as e:
            print(f"❌ Error signing in: {e}")
            return False
    else:
        print("❌ VERIFICATION_CODE environment variable not set")
        print("💡 After getting code, add VERIFICATION_CODE to environment variables and redeploy")
        return False

async def handle_2fa():
    """2FA password handle karta hai"""
    password = os.environ.get('TWO_FA_PASSWORD', '')
    if password:
        print("🔒 Signing in with 2FA password...")
        try:
            await client.sign_in(password=password)
            print("✅ Signed in with 2FA successfully!")
            return True
        except Exception as e:
            print(f"❌ 2FA signin error: {e}")
            return False
    else:
        print("⚠️  TWO_FA_PASSWORD not set (if you have 2FA enabled)")
        return True  # Skip if no 2FA

async def setup_client():
    """Client setup karta hai without interactive input"""
    print("🔐 Setting up Telegram client...")
    
    if not await client.is_user_authorized():
        print("👤 User not authorized. Starting authentication...")
        
        # Step 1: Send code request
        await send_code_request()
        
        # Step 2: Sign in with code
        if not await sign_in_with_code():
            return False
        
        # Step 3: Handle 2FA if needed
        if not await handle_2fa():
            return False
    else:
        print("✅ User already authorized")
    
    return True

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
    print("🔐 Starting Telegram authentication...")
    
    # Setup client without interactive input
    if not await setup_client():
        print("❌ Authentication failed. Please check environment variables.")
        return
    
    await detect_owner()
    asyncio.create_task(smart_monitor())
    
    print("✅ Render.com Bot Started Successfully!")
    print("🤖 Smart Auto-Toggle Features Active!")
    print("🌐 Bot is running 24/7 on Render!")
    
    # Keep the bot running
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Please check your environment variables and redeploy")