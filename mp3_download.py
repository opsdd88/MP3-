import os
import logging
import tempfile
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "***************************"

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    wait_msg = None
    audio_file = None
  
    if not any(domain in url for domain in ['youtube.com', 'youtu.be']):
        await update.message.reply_text("សូមបញ្ចូល YouTube URL ត្រឹមត្រូវ!")
        return
    
    try:
 
        wait_msg = await update.message.reply_text("⏳ Dowloading Mp3...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(tempfile.gettempdir(), '%(title).100s.%(ext)s'),
            'postprocessors': [],
            'writethumbnail': False,
            'quiet': True,
        }
        
  
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_file = ydl.prepare_filename(info)

            file_size = os.path.getsize(audio_file)
            if file_size > 45 * 1024 * 1024:
                await update.message.reply_text("ឯកសារធំពេក! សូមជ្រើសរើសវីដេអូខ្លីជាងនេះ។")
                if audio_file and os.path.exists(audio_file):
                    os.remove(audio_file)
                return

            if wait_msg:
                await wait_msg.delete()
                wait_msg = None

            with open(audio_file, 'rb') as audio:
                title = info.get('title', 'Audio')[:64]
                duration = info.get('duration', 0)
                uploader = info.get('uploader', 'Unknown')[:32]
                
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
                
                await update.message.reply_audio(
                    audio=audio,
                    title=title,
                    performer=uploader,
                    duration=duration,
                    caption=f"🎵 {title}\n👤 {uploader}\n⏱️ {duration_str}\nDeveloper : @mengheang25"
                )
            
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
        
    except yt_dlp.DownloadError as e:
        logger.error(f"Download Error: {e}")
        if wait_msg:
            await wait_msg.delete()
    except httpx.ConnectError as e:
        logger.error(f"Network Error: {e}")
        if wait_msg:
            await wait_msg.delete()
        await update.message.reply_text("🔌 បញ្ហាការតភ្ជាប់អ៊ីនធឺណិត! សូមព្យាយាមម្តងទៀត។")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        if wait_msg:
            await wait_msg.delete()
    finally:
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except Exception as e:
                logger.error(f"Error removing file: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when user sends /start command"""
    
    user = update.effective_user
    username = user.first_name if user.first_name else "there"
    
    welcome_text = f"""
🎵 **សួស្តី {username}! ខ្ញុំជា MP3 Downloader Bot** 🎵

**របៀបប្រើ:**
1. 📋 បញ្ចូល YouTube URL
2. ⏳ រង់ចាំបន្ដិច  
3. 📥 ទទួល file សម្លេង

**Developer:** @mengheang25

គ្រាន់តែបញ្ចូល YouTube URL របស់អ្នក!
/help /about
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message when user sends /help"""
    help_text = """
🆘 **ជំនួយ**

**របៀបប្រើ Bot:**
1. 🔗 ចម្លង YouTube URL ពី browser របស់អ្នក
2. 🤖 ផ្ញើ URL មក bot នេះ
3. ⏳ រង់ចាំ ការទាញយក
4. ✅ ទទួល ឯកសារសម្លេង

**URL ឧទាហរណ៍:**
- https://www.youtube.com/watch?v=xxxxxxxxxxx
- https://youtu.be/xxxxxxxxxxx

**កំហិត:**
- 📁 ឯកសារមិនលើសពី 50MB
- 🎵 ទាញយកតែសម្លេងប៉ុណ្ណោះ
    """
    await update.message.reply_text(help_text)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send about message when user sends /about"""
    about_text = """
🤖 **MP3 Downloader Bot**
⚡ **Turbo Mod Version**
🐍 **Created with Python**

**លក្ខណៈពិសេស:**
- ✅ ទាញយក MP3 ពី YouTube
- 🚀 ល្បឿនលឿន
- 🎯 សាមញ្ញនិងងាយស្រួល
- 🔧 មិនត្រូវការ FFmpeg

**Developer:** @mengheang25
    """
    await update.message.reply_text(about_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    text = update.message.text
    
    if any(domain in text for domain in ['youtube.com', 'youtu.be']):
        await download_audio(update, context)
    else:
        await update.message.reply_text("🤔 សូមផ្ញើ YouTube URL មកខ្ញុំ!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error_handler)
    
    print("=" * 50)
    print("🤖 MP3 Downloader Bot Started!")
    print("⚡ Turbo Mod Version")
    print("✅ Ready to download MP3 from YouTube")
    print("👤 Developer: @mengheang25")
    print("=" * 50)
    
    application.run_polling()

if __name__ == '__main__':
    main()