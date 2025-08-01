from config import Config
from rich.console import Console
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from database import DatabaseManager
from sender import TelegramSender


class TelegramBot:
    def __init__(self):
        self.sender = TelegramSender()
        self.db = DatabaseManager()
        self.console = Console()
        self.user_states = {}  # Track user conversation states

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use bot"""
        return user_id == Config.OWNER_ID

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user_id = update.effective_user.id

        if not self.is_authorized(user_id):
            await update.message.reply_text(Config.DEFAULT_TEMPLATES["unauthorized"])
            return

        keyboard = [
            [KeyboardButton("📱 مدیریت اکانت‌ها"), KeyboardButton("📤 ارسال پیام")],
            [KeyboardButton("📊 آنالیز و آمار"), KeyboardButton("⚙️ تنظیمات")],
            [KeyboardButton("📋 قالب‌های پیام"), KeyboardButton("🔍 جستجوی کاربران")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        welcome_text = f"""
🌟 **سلام {update.effective_user.first_name}!**

به ربات پیشرفته ارسال پیام خصوصی تلگرام خوش آمدید.

**قابلیت‌های اصلی:**
• 📱 مدیریت چندین اکانت تلگرام
• 📤 ارسال پیام خصوصی به کاربران
• 📊 آنالیز پیشرفته و آمارگیری
• 🔄 ارسال گروهی با کنترل سرعت
• 📋 مدیریت قالب‌های پیام
• 🔍 جستجوی پیشرفته کاربران

برای شروع، از منوی زیر استفاده کنید:
        """

        await update.message.reply_text(
            welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_account_management(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle account management"""
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت جدید", callback_data="add_account")],
            [InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data="list_accounts")],
            [
                InlineKeyboardButton(
                    "🔄 بارگذاری مجدد اکانت‌ها", callback_data="reload_accounts"
                )
            ],
            [InlineKeyboardButton("🏠 بازگشت به منو اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "📱 **مدیریت اکانت‌ها**\n\nلطفا عملیات مورد نظر را انتخاب کنید:"
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_message_sending(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle message sending options"""
        keyboard = [
            [InlineKeyboardButton("📨 ارسال پیام تکی", callback_data="send_single")],
            [InlineKeyboardButton("📤 ارسال گروهی", callback_data="send_bulk")],
            [InlineKeyboardButton("📋 استفاده از قالب", callback_data="send_template")],
            [InlineKeyboardButton("🏠 بازگشت به منو اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "📤 **ارسال پیام**\n\nنوع ارسال را انتخاب کنید:"
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_analytics(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle analytics and statistics"""
        analytics = self.sender.get_analytics(7)

        # Create analytics text
        text = "📊 **آنالیز و آمار (7 روز گذشته)**\n\n"

        if analytics["daily_stats"]:
            text += "📈 **آمار روزانه:**\n"
            for day_stat in analytics["daily_stats"][:5]:  # Show last 5 days
                text += f"• {day_stat[0]}: {day_stat[1]} پیام ({day_stat[2]} موفق، {day_stat[3]} ناموفق)\n"

        text += "\n👥 **آمار اکانت‌ها:**\n"
        if analytics["account_stats"]:
            for acc_stat in analytics["account_stats"]:
                text += f"• {acc_stat[0]}: {acc_stat[2]} کل، {acc_stat[3]} امروز\n"
        else:
            text += "هیچ اکانتی یافت نشد.\n"

        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 آمار تفصیلی", callback_data="detailed_analytics"
                )
            ],
            [InlineKeyboardButton("📈 نمودار آمار", callback_data="analytics_chart")],
            [InlineKeyboardButton("🏠 بازگشت به منو اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def callback_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle callback queries"""
        query = update.callback_query
        user_id = query.from_user.id

        if not self.is_authorized(user_id):
            await query.answer("شما مجاز به استفاده از این ربات نیستید.")
            return

        await query.answer()

        if query.data == "add_account":
            await self.start_add_account(query, context)
        elif query.data == "list_accounts":
            await self.show_accounts_list(query, context)
        elif query.data == "reload_accounts":
            await self.reload_accounts(query, context)
        elif query.data == "send_single":
            await self.start_single_send(query, context)
        elif query.data == "send_bulk":
            await self.start_bulk_send(query, context)
        elif query.data == "main_menu":
            await self.show_main_menu(query, context)

    async def start_add_account(self, query, context):
        """Start adding new account process"""
        text = """
📱 **افزودن اکانت جدید**

برای افزودن اکانت جدید، لطفا اطلاعات زیر را به ترتیب ارسال کنید:

1️⃣ شماره تلفن (مثال: +989123456789)
2️⃣ API ID
3️⃣ API Hash

ابتدا شماره تلفن خود را ارسال کنید:
        """

        self.user_states[query.from_user.id] = {
            "action": "add_account",
            "step": "phone",
        }
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

    async def show_accounts_list(self, query, context):
        """Show list of accounts"""
        accounts = self.sender.get_accounts_list()

        if not accounts:
            text = "📱 **لیست اکانت‌ها**\n\nهیچ اکانتی یافت نشد. لطفا ابتدا اکانت اضافه کنید."
        else:
            text = "📱 **لیست اکانت‌ها**\n\n"
            for i, account in enumerate(accounts, 1):
                status = "🟢 فعال" if account["is_active"] else "🔴 غیرفعال"
                name = f"{account['first_name'] or ''} {account['last_name'] or ''}".strip()
                text += f"{i}. {name} ({account['phone']})\n"
                text += f"   {status} | کل ارسالی: {account['total_sent']}\n\n"

        keyboard = [[InlineKeyboardButton("🏠 بازگشت", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def reload_accounts(self, query, context):
        """Reload all accounts"""
        try:
            await self.sender.load_accounts()
            text = "✅ تمام اکانت‌ها با موفقیت بارگذاری شدند."
        except Exception as e:
            text = f"❌ خطا در بارگذاری اکانت‌ها: {str(e)}"

        keyboard = [[InlineKeyboardButton("🏠 بازگشت", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup)

    async def start_single_send(self, query, context):
        """Start single message sending"""
        accounts = self.sender.get_accounts_list()

        if not accounts:
            text = "❌ هیچ اکانتی یافت نشد. لطفا ابتدا اکانت اضافه کنید."
            keyboard = [[InlineKeyboardButton("🏠 بازگشت", callback_data="main_menu")]]
        else:
            text = "📨 **ارسال پیام تکی**\n\nاکانت مورد نظر را انتخاب کنید:"
            keyboard = []
            for account in accounts[:10]:  # Show max 10 accounts
                name = f"{account['first_name'] or ''} {account['last_name'] or ''}".strip()
                button_text = f"{name} ({account['phone']})"
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            button_text, callback_data=f"select_account_{account['id']}"
                        )
                    ]
                )
            keyboard.append(
                [InlineKeyboardButton("🏠 بازگشت", callback_data="main_menu")]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def show_main_menu(self, query, context):
        """Show main menu"""
        keyboard = [
            [KeyboardButton("📱 مدیریت اکانت‌ها"), KeyboardButton("📤 ارسال پیام")],
            [KeyboardButton("📊 آنالیز و آمار"), KeyboardButton("⚙️ تنظیمات")],
            [KeyboardButton("📋 قالب‌های پیام"), KeyboardButton("🔍 جستجوی کاربران")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        text = "🏠 **منوی اصلی**\n\nلطفا گزینه مورد نظر را انتخاب کنید:"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_message(
            query.from_user.id, "منوی اصلی:", reply_markup=reply_markup
        )

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id

        if not self.is_authorized(user_id):
            await update.message.reply_text(Config.DEFAULT_TEMPLATES["unauthorized"])
            return

        text = update.message.text

        # Handle menu buttons
        if text == "📱 مدیریت اکانت‌ها":
            await self.handle_account_management(update, context)
        elif text == "📤 ارسال پیام":
            await self.handle_message_sending(update, context)
        elif text == "📊 آنالیز و آمار":
            await self.handle_analytics(update, context)
        elif text == "📋 قالب‌های پیام":
            await self.handle_templates(update, context)
        elif text == "🔍 جستجوی کاربران":
            await self.handle_user_search(update, context)
        else:
            # Handle user states for multi-step operations
            if user_id in self.user_states:
                await self.handle_user_state(update, context)
            else:
                await update.message.reply_text("لطفا از منوی اصلی استفاده کنید.")

    async def handle_user_state(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle user conversation states"""
        user_id = update.effective_user.id
        state = self.user_states[user_id]
        text = update.message.text

        if state["action"] == "add_account":
            if state["step"] == "phone":
                state["phone"] = text
                state["step"] = "api_id"
                await update.message.reply_text(
                    "✅ شماره تلفن دریافت شد.\n\n2️⃣ حالا API ID را ارسال کنید:"
                )

            elif state["step"] == "api_id":
                try:
                    state["api_id"] = int(text)
                    state["step"] = "api_hash"
                    await update.message.reply_text(
                        "✅ API ID دریافت شد.\n\n3️⃣ حالا API Hash را ارسال کنید:"
                    )
                except ValueError:
                    await update.message.reply_text(
                        "❌ API ID باید عدد باشد. دوباره تلاش کنید:"
                    )

            elif state["step"] == "api_hash":
                state["api_hash"] = text
                await update.message.reply_text(
                    "⏳ در حال افزودن اکانت... لطفا صبر کنید."
                )

                # Add account
                result = await self.sender.add_account(
                    phone=state["phone"],
                    api_id=state["api_id"],
                    api_hash=state["api_hash"],
                )

                if result["success"]:
                    user_info = result["user_info"]
                    text = f"""
✅ **اکانت با موفقیت اضافه شد!**

👤 **اطلاعات کاربر:**
• نام: {user_info['first_name']} {user_info['last_name'] or ''}
• یوزرنیم: @{user_info['username'] or 'ندارد'}
• شماره: {user_info['phone']}

اکانت آماده استفاده است.
                    """
                else:
                    text = f"❌ خطا در افزودن اکانت: {result['error']}"

                await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
                del self.user_states[user_id]

    async def handle_templates(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle message templates"""
        templates = self.db.get_templates()

        if not templates:
            text = "📋 **قالب‌های پیام**\n\nهیچ قالبی یافت نشد."
        else:
            text = "📋 **قالب‌های پیام**\n\n"
            for template in templates:
                text += f"• **{template['name']}**\n"
                text += f"  {template['content'][:50]}...\n\n"

        keyboard = [
            [InlineKeyboardButton("➕ افزودن قالب جدید", callback_data="add_template")],
            [InlineKeyboardButton("🏠 بازگشت به منو اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_user_search(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle user search"""
        text = """
🔍 **جستجوی کاربران**

برای جستجوی کاربران، ابتدا اکانت مورد نظر و سپس کلمه کلیدی جستجو را ارسال کنید.

این ویژگی به زودی فعال خواهد شد...
        """
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.callback_handler))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler)
        )

        # Start the bot
        print("🚀 ربات در حال اجرا...")
        application.run_polling()


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
