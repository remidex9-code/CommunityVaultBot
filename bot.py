import os
import logging
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            category TEXT,
            url TEXT,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

# /start command handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        "📚 **Welcome to Community Vault Bot!**\n\n"
        "Turn your group chat into a shared knowledge base.\n\n"
        "**Available Commands:**\n"
        "• `/add [category] [url] [description]` — Add a new resource\n"
        "• `/search [keyword]` — Search stored links\n"
        "• `/categories` — View list of categories in this chat"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# /add command handler: /add [category] [url] [description...]
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    
    # Check if arguments are provided
    if len(context.args) < 3:
        await update.message.reply_text(
            "⚠️ **Format:** `/add [category] [url] [description]`\n\n"
            "**Example:** `/add forex https://example.com Great economic calendar`",
            parse_mode="Markdown"
        )
        return

    category = context.args[0].lower()
    url = context.args[1]
    description = " ".join(context.args[2:])

    # Save resource into SQLite database
    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resources (chat_id, category, url, description) VALUES (?, ?, ?, ?)",
        (chat_id, category, url, description)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Resource added under `#{category}`!", parse_mode="Markdown")

# /search command handler: /search [keyword or category]
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text("⚠️ Please provide a keyword or category to search.\nExample: `/search forex`", parse_mode="Markdown")
        return

    query = f"%{context.args[0].lower()}%"

    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute(
        """SELECT category, url, description FROM resources 
           WHERE chat_id = ? AND (LOWER(category) LIKE ? OR LOWER(description) LIKE ?) 
           LIMIT 5""",
        (chat_id, query, query)
    )
    results = cursor.fetchall()
    conn.close()

    if not results:
        await update.message.reply_text("🔍 No resources found matching your search.")
        return

    response = "🔍 **Found Resources:**\n\n"
    for cat, url, desc in results:
        response += f"🏷️ *#{cat}*\n📝 {desc}\n🔗 {url}\n\n"

    await update.message.reply_text(response, parse_mode="Markdown")

# /categories command handler
async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    conn = sqlite3.connect("vault.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM resources WHERE chat_id = ?", (chat_id,))
    cats = cursor.fetchall()
    conn.close()

    if not cats:
        await update.message.reply_text("📂 No categories found yet. Add resources using `/add`!", parse_mode="Markdown")
        return

    cat_list = "\n".join([f"• `{c[0]}`" for c in cats])
    await update.message.reply_text(f"📂 **Categories in this vault:**\n\n{cat_list}", parse_mode="Markdown")

def main() -> None:
    init_db()
    
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN variable is missing!")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("categories", categories_command))

    print("Community Vault Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
