import asyncio
import os

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
        self.analysis_tasks = {}  # Track analysis tasks
        self.sending_tasks = {}  # Track sending tasks

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use bot"""
        return user_id == Config.OWNER_ID

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user_id = update.effective_user.id

        if not self.is_authorized(user_id):
            await update.message.reply_text(Config.MESSAGES["unauthorized"])
            return

        keyboard = [
            [KeyboardButton("📱 مدیریت اکانت‌ها"), KeyboardButton("📊 آنالیز پیشرفته")],
            [KeyboardButton("📤 ارسال به پیوی"), KeyboardButton("🏷️ ایجاد دسته‌بندی")],
            [KeyboardButton("⚙️ تنظیمات"), KeyboardButton("🌐 مدیریت پروکسی")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            Config.MESSAGES["welcome"],
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def handle_account_management(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle account management menu"""
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account")],
            [InlineKeyboardButton("📋 وضعیت اکانت‌ها", callback_data="account_status")],
            [InlineKeyboardButton("🔄 بارگذاری مجدد", callback_data="reload_accounts")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "📱 **مدیریت اکانت‌ها**\n\nعملیات مورد نظر را انتخاب کنید:"
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_advanced_analysis(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle advanced analysis menu"""
        accounts = self.db.get_accounts()
        if not accounts:
            await update.message.reply_text("❌ ابتدا اکانت اضافه کنید!")
            return

        keyboard = []
        for account in accounts:
            display_name = f"{account['first_name'] or account['phone']} ({Config.ACCOUNT_STATUS.get(account['status'], account['status'])})"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        display_name, callback_data=f"analyze_{account['id']}"
                    )
                ]
            )

        keyboard.append(
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "📊 **آنالیز پیشرفته**\n\nبا کدام اکانت می‌خواهید آنالیز کنید؟"
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_private_messaging(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle private messaging menu"""
        categories = self.db.get_categories()
        if not categories:
            await update.message.reply_text("❌ ابتدا دسته‌بندی ایجاد کنید!")
            return

        keyboard = []
        for category in categories:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{category['name']} ({category['account_count']} اکانت)",
                        callback_data=f"send_category_{category['id']}",
                    )
                ]
            )

        keyboard.append(
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "📤 **ارسال به پیوی**\n\nبا کدام دسته‌بندی می‌خواهید ارسال کنید؟"
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_category_creation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle category creation"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ ایجاد دسته جدید", callback_data="create_category"
                )
            ],
            [InlineKeyboardButton("📋 مشاهده دسته‌ها", callback_data="view_categories")],
            [
                InlineKeyboardButton(
                    "🔄 تخصیص اکانت به دسته", callback_data="assign_category"
                )
            ],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "🏷️ **مدیریت دسته‌بندی**\n\nعملیات مورد نظر را انتخاب کنید:"
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle settings menu"""
        current_settings = self.db.get_all_settings()

        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 تعداد ارسال به پیوی", callback_data="setting_send_limit"
                )
            ],
            [
                InlineKeyboardButton(
                    "⏰ زمان استراحت اکانت", callback_data="setting_account_rest"
                )
            ],
            [InlineKeyboardButton("🌐 تنظیمات پروکسی", callback_data="setting_proxy")],
            [
                InlineKeyboardButton(
                    "🔢 توزیع هش روی اکانت‌ها", callback_data="setting_hash_distribution"
                )
            ],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Show current settings
        send_limit = current_settings.get("send_limit", Config.DEFAULT_SEND_LIMIT)
        account_rest = current_settings.get("account_rest", Config.DEFAULT_ACCOUNT_REST)

        text = f"""⚙️ **تنظیمات سیستم**

📊 **تعداد ارسال فعلی:** {send_limit} پیام در هر جلسه
⏰ **زمان استراحت:** {account_rest} ثانیه
🌐 **پروکسی:** {'فعال' if current_settings.get('proxy_enabled') == 'true' else 'غیرفعال'}

عملیات مورد نظر را انتخاب کنید:"""

        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_proxy_management(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle proxy management"""
        keyboard = [
            [InlineKeyboardButton("➕ افزودن پروکسی", callback_data="add_proxy")],
            [InlineKeyboardButton("📋 لیست پروکسی‌ها", callback_data="list_proxies")],
            [InlineKeyboardButton("🔄 تخصیص پروکسی", callback_data="assign_proxy")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = "🌐 **مدیریت پروکسی**\n\nعملیات مورد نظر را انتخاب کنید:"
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def callback_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()

        data = query.data
        query.from_user.id

        # Main menu
        if data == "main_menu":
            await self.show_main_menu(query)

        # Account management
        elif data == "add_account":
            await self.start_add_account(query, context)
        elif data == "account_status":
            await self.show_account_status(query)
        elif data == "reload_accounts":
            await self.reload_accounts(query)

        # Analysis
        elif data.startswith("analyze_"):
            account_id = int(data.split("_")[1])
            await self.start_analysis(query, context, account_id)
        elif data.startswith("stop_analysis_"):
            account_id = int(data.split("_")[2])
            await self.stop_analysis(query, account_id)

        # Categories
        elif data == "create_category":
            await self.start_create_category(query, context)
        elif data == "view_categories":
            await self.show_categories(query)
        elif data == "assign_category":
            await self.start_assign_category(query, context)

        # Private messaging
        elif data.startswith("send_category_"):
            category_id = int(data.split("_")[2])
            await self.start_private_messaging(query, context, category_id)
        elif data.startswith("stop_sending_"):
            category_id = int(data.split("_")[2])
            await self.stop_sending(query, category_id)

        # Settings
        elif data.startswith("setting_"):
            setting_type = data.split("_", 1)[1]
            await self.handle_setting_change(query, context, setting_type)

        # Proxy management
        elif data == "add_proxy":
            await self.start_add_proxy(query, context)
        elif data == "list_proxies":
            await self.show_proxies(query)
        elif data == "assign_proxy":
            await self.start_assign_proxy(query, context)

    async def show_main_menu(self, query):
        """Show main menu"""
        keyboard = [
            [KeyboardButton("📱 مدیریت اکانت‌ها"), KeyboardButton("📊 آنالیز پیشرفته")],
            [KeyboardButton("📤 ارسال به پیوی"), KeyboardButton("🏷️ ایجاد دسته‌بندی")],
            [KeyboardButton("⚙️ تنظیمات"), KeyboardButton("🌐 مدیریت پروکسی")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await query.edit_message_text(
            Config.MESSAGES["welcome"],
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def start_add_account(self, query, context):
        """Start adding new account"""
        self.user_states[query.from_user.id] = {
            "action": "add_account",
            "step": "phone",
        }

        await query.edit_message_text(
            "📱 **افزودن اکانت جدید**\n\nشماره تلفن اکانت را وارد کنید:\n\n(مثال: +989123456789)"
        )

    async def show_account_status(self, query):
        """Show account status with rep/non-rep info"""
        accounts = self.db.get_accounts()
        if not accounts:
            await query.edit_message_text("❌ هیچ اکانتی یافت نشد!")
            return

        # Count accounts by status
        status_counts = {}
        for account in accounts:
            status = account["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        # Generate status text
        text = "📱 **وضعیت اکانت‌ها**\n\n"

        # Summary
        text += "📊 **خلاصه:**\n"
        for status, count in status_counts.items():
            status_emoji = Config.ACCOUNT_STATUS.get(status, status)
            text += f"• {status_emoji}: {count} اکانت\n"

        text += f"\n🔢 **کل اکانت‌ها:** {len(accounts)}\n\n"

        # Detailed list
        text += "📋 **جزئیات:**\n"
        for i, account in enumerate(accounts[:10], 1):  # Show first 10
            name = account["first_name"] or account["phone"]
            status_emoji = Config.ACCOUNT_STATUS.get(
                account["status"], account["status"]
            )
            premium_emoji = "💎" if account.get("is_premium") else ""
            category = account.get("category_name", "بدون دسته")

            text += f"{i}. {name} {premium_emoji}\n"
            text += f"   └ {status_emoji} | دسته: {category}\n"
            text += f"   └ کد: {account['id']} | ارسال: {account['total_sent']}\n\n"

        if len(accounts) > 10:
            text += f"... و {len(accounts) - 10} اکانت دیگر"

        keyboard = [
            [InlineKeyboardButton("🔄 به‌روزرسانی", callback_data="account_status")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def start_analysis(self, query, context, account_id):
        """Start member analysis"""
        account = next(
            (acc for acc in self.db.get_accounts() if acc["id"] == account_id), None
        )
        if not account:
            await query.edit_message_text("❌ اکانت یافت نشد!")
            return

        self.user_states[query.from_user.id] = {
            "action": "analysis",
            "account_id": account_id,
            "step": "get_chat",
        }

        keyboard = [
            [
                InlineKeyboardButton(
                    "⏹️ توقف آنالیز", callback_data=f"stop_analysis_{account_id}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = f"""🔍 **شروع آنالیز با اکانت:**
{account['first_name'] or account['phone']}

لطفا لینک یا آیدی گروه/کانال را ارسال کنید:
(مثال: @channel_name یا https://t.me/channel_name)"""

        await query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def start_private_messaging(self, query, context, category_id):
        """Start private messaging process"""
        category = next(
            (cat for cat in self.db.get_categories() if cat["id"] == category_id), None
        )
        if not category:
            await query.edit_message_text("❌ دسته‌بندی یافت نشد!")
            return

        accounts = self.db.get_accounts(category_id)
        if not accounts:
            await query.edit_message_text("❌ هیچ اکانتی در این دسته یافت نشد!")
            return

        self.user_states[query.from_user.id] = {
            "action": "private_messaging",
            "category_id": category_id,
            "step": "get_members",
        }

        keyboard = [
            [
                InlineKeyboardButton(
                    "⏹️ توقف ارسال", callback_data=f"stop_sending_{category_id}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = f"""📤 **ارسال با دسته:** {category['name']}
💼 **تعداد اکانت:** {len(accounts)}

مرحله 1: لیست ممبرها را ارسال کنید
(هر آیدی عددی در خط جداگانه)"""

        await query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN
        )

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id

        if not self.is_authorized(user_id):
            return

        # Handle menu buttons
        text = update.message.text

        if text == "📱 مدیریت اکانت‌ها":
            await self.handle_account_management(update, context)
        elif text == "📊 آنالیز پیشرفته":
            await self.handle_advanced_analysis(update, context)
        elif text == "📤 ارسال به پیوی":
            await self.handle_private_messaging(update, context)
        elif text == "🏷️ ایجاد دسته‌بندی":
            await self.handle_category_creation(update, context)
        elif text == "⚙️ تنظیمات":
            await self.handle_settings(update, context)
        elif text == "🌐 مدیریت پروکسی":
            await self.handle_proxy_management(update, context)

        # Handle user states
        elif user_id in self.user_states:
            await self.handle_user_state(update, context)

    async def handle_user_state(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle user conversation states"""
        user_id = update.effective_user.id
        state = self.user_states[user_id]
        text = update.message.text

        if state["action"] == "add_account":
            await self.handle_add_account_state(update, context, state, text)
        elif state["action"] == "analysis":
            await self.handle_analysis_state(update, context, state, text)
        elif state["action"] == "private_messaging":
            await self.handle_messaging_state(update, context, state, text)
        elif state["action"] == "create_category":
            await self.handle_category_state(update, context, state, text)
        elif state["action"] == "settings":
            await self.handle_settings_state(update, context, state, text)

    async def handle_add_account_state(self, update, context, state, text):
        """Handle add account conversation"""
        if state["step"] == "phone":
            state["phone"] = text.strip()
            state["step"] = "api_id"
            await update.message.reply_text("📱 API ID را وارد کنید:")

        elif state["step"] == "api_id":
            try:
                state["api_id"] = int(text.strip())
                state["step"] = "api_hash"
                await update.message.reply_text("🔑 API Hash را وارد کنید:")
            except ValueError:
                await update.message.reply_text("❌ API ID باید عدد باشد!")

        elif state["step"] == "api_hash":
            state["api_hash"] = text.strip()

            # Add account to sender and database
            try:
                success = await self.sender.add_account(
                    state["phone"], state["api_id"], state["api_hash"]
                )

                if success:
                    # Auto-assign proxy if available
                    proxy = self.db.get_available_proxy()
                    proxy_id = proxy["id"] if proxy else None

                    account_id = self.db.add_account(
                        state["phone"],
                        state["phone"].replace("+", ""),
                        state["api_id"],
                        state["api_hash"],
                    )

                    if proxy_id:
                        self.db.assign_proxy_to_account(account_id, proxy_id)

                    await update.message.reply_text(Config.MESSAGES["account_added"])
                else:
                    await update.message.reply_text(
                        Config.MESSAGES["account_error"].format("خطا در اتصال")
                    )

            except Exception as e:
                await update.message.reply_text(
                    Config.MESSAGES["account_error"].format(str(e))
                )

            # Clear state
            del self.user_states[update.effective_user.id]

    async def handle_analysis_state(self, update, context, state, text):
        """Handle analysis conversation"""
        if state["step"] == "get_chat":
            try:
                # Start analysis task
                account_id = state["account_id"]
                chat_identifier = text.strip()

                # Create analysis task
                task = asyncio.create_task(
                    self.sender.extract_members(account_id, chat_identifier)
                )
                self.analysis_tasks[account_id] = task

                await update.message.reply_text(Config.MESSAGES["analysis_started"])

                # Wait for completion
                members = await task

                if members:
                    # Save members to database
                    self.db.save_members(members, account_id)

                    # Send member list
                    member_text = "👥 **لیست ممبرها:**\n\n"
                    for i, member in enumerate(members[:50], 1):  # Show first 50
                        member_text += f"{i}. {member.get('id', 'N/A')}\n"

                    if len(members) > 50:
                        member_text += f"\n... و {len(members) - 50} ممبر دیگر"

                    await update.message.reply_text(
                        Config.MESSAGES["analysis_completed"].format(len(members))
                    )
                    await update.message.reply_text(
                        member_text, parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await update.message.reply_text("❌ هیچ ممبری یافت نشد!")

                # Clean up
                if account_id in self.analysis_tasks:
                    del self.analysis_tasks[account_id]
                del self.user_states[update.effective_user.id]

            except Exception as e:
                await update.message.reply_text(f"❌ خطا در آنالیز: {str(e)}")
                del self.user_states[update.effective_user.id]

    async def handle_messaging_state(self, update, context, state, text):
        """Handle private messaging conversation"""
        if state["step"] == "get_members":
            try:
                # Parse member IDs
                member_ids = []
                for line in text.strip().split("\n"):
                    line = line.strip()
                    if line.isdigit():
                        member_ids.append(int(line))

                if not member_ids:
                    await update.message.reply_text("❌ هیچ آیدی معتبری یافت نشد!")
                    return

                state["member_ids"] = member_ids
                state["step"] = "get_message"

                await update.message.reply_text(
                    f"✅ {len(member_ids)} ممبر پردازش شد!\n\n"
                    "مرحله 2: پیام یا بنر خود را ارسال کنید:\n"
                    "(متن، عکس، ویدیو و ... پشتیبانی می‌شود)"
                )

            except Exception as e:
                await update.message.reply_text(f"❌ خطا در پردازش لیست: {str(e)}")

        elif state["step"] == "get_message":
            try:
                # Start sending task
                category_id = state["category_id"]
                member_ids = state["member_ids"]

                # Handle media or text
                media_path = None
                message_text = text

                if update.message.photo:
                    # Handle photo
                    photo = update.message.photo[-1]
                    file = await context.bot.get_file(photo.file_id)
                    media_path = os.path.join(Config.MEDIA_DIR, f"{photo.file_id}.jpg")
                    await file.download_to_drive(media_path)
                    message_text = update.message.caption or ""

                elif update.message.video:
                    # Handle video
                    video = update.message.video
                    file = await context.bot.get_file(video.file_id)
                    media_path = os.path.join(Config.MEDIA_DIR, f"{video.file_id}.mp4")
                    await file.download_to_drive(media_path)
                    message_text = update.message.caption or ""

                # Create sending task
                task = asyncio.create_task(
                    self.sender.send_bulk_messages(
                        category_id, member_ids, message_text, media_path
                    )
                )
                self.sending_tasks[category_id] = task

                await update.message.reply_text(Config.MESSAGES["sending_started"])

                # Wait for completion
                results = await task

                success_count = sum(1 for r in results if r["status"] == "success")
                total_count = len(results)

                await update.message.reply_text(
                    f"✅ ارسال کامل شد!\n" f"موفق: {success_count}/{total_count}"
                )

                # Clean up
                if category_id in self.sending_tasks:
                    del self.sending_tasks[category_id]
                del self.user_states[update.effective_user.id]

            except Exception as e:
                await update.message.reply_text(f"❌ خطا در ارسال: {str(e)}")
                del self.user_states[update.effective_user.id]

    async def stop_analysis(self, query, account_id):
        """Stop analysis task"""
        if account_id in self.analysis_tasks:
            self.analysis_tasks[account_id].cancel()
            del self.analysis_tasks[account_id]
            await query.edit_message_text(Config.MESSAGES["analysis_stopped"])
        else:
            await query.edit_message_text("❌ هیچ آنالیز فعالی یافت نشد!")

    async def stop_sending(self, query, category_id):
        """Stop sending task"""
        if category_id in self.sending_tasks:
            self.sending_tasks[category_id].cancel()
            del self.sending_tasks[category_id]
            await query.edit_message_text(Config.MESSAGES["sending_stopped"])
        else:
            await query.edit_message_text("❌ هیچ ارسال فعالی یافت نشد!")

    async def start_create_category(self, query, context):
        """Start creating new category"""
        self.user_states[query.from_user.id] = {
            "action": "create_category",
            "step": "name",
        }

        await query.edit_message_text(
            "🏷️ **ایجاد دسته‌بندی جدید**\n\nنام دسته‌بندی را وارد کنید:"
        )

    async def handle_category_state(self, update, context, state, text):
        """Handle category creation conversation"""
        if state["step"] == "name":
            try:
                self.db.create_category(text.strip())
                await update.message.reply_text(Config.MESSAGES["category_created"])
                del self.user_states[update.effective_user.id]
            except Exception as e:
                await update.message.reply_text(f"❌ خطا در ایجاد دسته: {str(e)}")

    def setup_handlers(self, application):
        """Setup bot handlers"""
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.callback_handler))
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler)
        )
        application.add_handler(
            MessageHandler(filters.PHOTO | filters.VIDEO, self.message_handler)
        )
