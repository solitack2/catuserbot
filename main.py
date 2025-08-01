#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Telegram Private Message Sender Bot
============================================

ربات پیشرفته ارسال پیام خصوصی تلگرام با قابلیت‌های:
• مدیریت چندین اکانت تلگرام
• آنالیز پیشرفته ممبرها
• ارسال پیام خصوصی با پشتیبانی رسانه
• دسته‌بندی اکانت‌ها
• مدیریت پروکسی
• تنظیمات پیشرفته

Author: AI Assistant
Version: 2.0.0
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from config import Config
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from telegram.ext import Application

from bot import TelegramBot
from database import DatabaseManager
from sender import TelegramSender

console = Console()


class TelegramSenderApp:
    def __init__(self):
        self.bot = None
        self.sender = None
        self.db = None
        self.application = None
        self.running = False

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            console.print("\n[yellow]🛑 در حال خروج از برنامه...[/yellow]")
            self.running = False
            if self.sender:
                asyncio.create_task(self.sender.cleanup_clients())
                asyncio.create_task(self.sender.stop_all_tasks())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def show_banner(self):
        """Show application banner"""
        banner_text = """
🤖 ربات پیشرفته ارسال پیام تلگرام
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 مدیریت اکانت‌ها
📊 آنالیز پیشرفته ممبرها  
📤 ارسال پیام خصوصی
🏷️ دسته‌بندی اکانت‌ها
🌐 مدیریت پروکسی
⚙️ تنظیمات پیشرفته

ورژن: 2.0.0
        """

        panel = Panel(
            banner_text,
            title="[bold blue]🚀 Telegram Sender Bot[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )
        console.print(panel)

    def show_status(self):
        """Show current system status"""
        try:
            # Get statistics
            accounts = self.db.get_accounts()
            categories = self.db.get_categories()
            proxies = self.db.get_proxies()

            # Create status table
            table = Table(
                title="📊 وضعیت سیستم", show_header=True, header_style="bold magenta"
            )
            table.add_column("بخش", style="cyan", width=15)
            table.add_column("تعداد", style="green", width=10)
            table.add_column("وضعیت", style="yellow", width=20)

            # Account statistics
            active_accounts = len(
                [acc for acc in accounts if acc["status"] == "active"]
            )
            table.add_row(
                "🔐 اکانت‌ها",
                str(len(accounts)),
                f"{active_accounts} فعال از {len(accounts)}",
            )

            # Category statistics
            table.add_row("🏷️ دسته‌بندی", str(len(categories)), "آماده استفاده")

            # Proxy statistics
            active_proxies = len([p for p in proxies if p["is_active"]])
            table.add_row(
                "🌐 پروکسی",
                str(len(proxies)),
                f"{active_proxies} فعال از {len(proxies)}",
            )

            # Settings status
            settings = self.db.get_all_settings()
            send_limit = settings.get("send_limit", Config.DEFAULT_SEND_LIMIT)
            table.add_row("⚙️ تنظیمات", "✅", f"حد ارسال: {send_limit}")

            console.print(table)

        except Exception as e:
            console.print(f"[red]❌ خطا در نمایش وضعیت: {str(e)}[/red]")

    def check_config(self):
        """Check configuration and setup"""
        config_ok = True

        # Check bot token
        if Config.BOT_TOKEN == "YOUR_BOT_TOKEN":
            console.print("[red]❌ BOT_TOKEN تنظیم نشده است![/red]")
            console.print(
                "[yellow]💡 BOT_TOKEN را در فایل .env یا config.py تنظیم کنید[/yellow]"
            )
            config_ok = False

        # Check owner ID
        if Config.OWNER_ID == 123456789:
            console.print("[red]❌ OWNER_ID تنظیم نشده است![/red]")
            console.print(
                "[yellow]💡 OWNER_ID را در فایل .env یا config.py تنظیم کنید[/yellow]"
            )
            config_ok = False

        # Check directories
        for directory in [Config.SESSIONS_DIR, Config.MEDIA_DIR, Config.LOGS_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                console.print(f"[green]✅ پوشه {directory} ایجاد شد[/green]")

        return config_ok

    def setup_logging(self):
        """Setup application logging"""
        log_file = os.path.join(Config.LOGS_DIR, "main.log")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

        # Reduce pyrogram logging
        logging.getLogger("pyrogram").setLevel(logging.WARNING)

        console.print(f"[green]✅ لاگ‌ها در {log_file} ذخیره می‌شوند[/green]")

    async def initialize_components(self):
        """Initialize all components"""
        try:
            console.print("[blue]🔧 در حال راه‌اندازی اجزای سیستم...[/blue]")

            # Initialize database
            self.db = DatabaseManager()
            console.print("[green]✅ پایگاه داده آماده شد[/green]")

            # Initialize sender
            self.sender = TelegramSender()
            console.print("[green]✅ سیستم ارسال آماده شد[/green]")

            # Initialize bot
            self.bot = TelegramBot()
            console.print("[green]✅ ربات تلگرام آماده شد[/green]")

            # Setup telegram application
            self.application = Application.builder().token(Config.BOT_TOKEN).build()
            self.bot.setup_handlers(self.application)
            console.print("[green]✅ هندلرهای ربات تنظیم شدند[/green]")

            return True

        except Exception as e:
            console.print(f"[red]❌ خطا در راه‌اندازی: {str(e)}[/red]")
            return False

    async def start_bot(self):
        """Start the telegram bot"""
        try:
            console.print("[blue]🚀 در حال شروع ربات تلگرام...[/blue]")

            # Start the application
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            self.running = True
            console.print("[green]✅ ربات با موفقیت شروع شد![/green]")
            console.print(
                f"[yellow]📱 ربات در حال اجرا است. برای خروج Ctrl+C بزنید[/yellow]"
            )

            # Keep running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            console.print(f"[red]❌ خطا در اجرای ربات: {str(e)}[/red]")
            raise

    async def shutdown(self):
        """Graceful shutdown"""
        try:
            console.print("[yellow]🛑 در حال خاموش کردن سیستم...[/yellow]")

            if self.sender:
                await self.sender.cleanup_clients()
                await self.sender.stop_all_tasks()
                console.print("[green]✅ اتصالات اکانت‌ها بسته شدند[/green]")

            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                console.print("[green]✅ ربات تلگرام خاموش شد[/green]")

            console.print("[green]✅ سیستم با موفقیت خاموش شد[/green]")

        except Exception as e:
            console.print(f"[red]❌ خطا در خاموش کردن: {str(e)}[/red]")

    def show_help(self):
        """Show help information"""
        help_text = """
📖 راهنمای استفاده:

1️⃣ **راه‌اندازی اولیه:**
   • BOT_TOKEN را از @BotFather دریافت و تنظیم کنید
   • OWNER_ID را (آیدی عددی تلگرام شما) تنظیم کنید
   • فایل .env ایجاد کنید یا config.py را ویرایش کنید

2️⃣ **افزودن اکانت:**
   • از منوی "مدیریت اکانت‌ها" استفاده کنید
   • API ID و API Hash از my.telegram.org دریافت کنید
   • اکانت‌ها به صورت خودکار به پروکسی تخصیص می‌یابند

3️⃣ **آنالیز ممبرها:**
   • از منوی "آنالیز پیشرفته" استفاده کنید
   • اکانت مورد نظر را انتخاب کنید
   • لینک گروه/کانال را ارسال کنید

4️⃣ **ارسال پیام:**
   • ابتدا دسته‌بندی ایجاد کنید
   • اکانت‌ها را به دسته تخصیص دهید
   • از منوی "ارسال به پیوی" استفاده کنید

5️⃣ **تنظیمات:**
   • حد ارسال، زمان استراحت و پروکسی را تنظیم کنید
   • توزیع هش روی اکانت‌ها را مدیریت کنید

📞 **پشتیبانی:**
   • لاگ‌ها در پوشه logs ذخیره می‌شوند
   • در صورت مشکل، لاگ‌ها را بررسی کنید
        """

        panel = Panel(
            help_text,
            title="[bold cyan]📖 راهنمای استفاده[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print(panel)

    async def run(self):
        """Main run method"""
        try:
            # Show banner
            self.show_banner()

            # Setup signal handlers
            self.setup_signal_handlers()

            # Setup logging
            self.setup_logging()

            # Check configuration
            if not self.check_config():
                console.print(
                    "\n[red]❌ پیکربندی کامل نیست. لطفا تنظیمات را بررسی کنید.[/red]"
                )
                self.show_help()
                return

            # Initialize components
            if not await self.initialize_components():
                console.print("\n[red]❌ خطا در راه‌اندازی اجزای سیستم[/red]")
                return

            # Show status
            self.show_status()

            # Start bot
            await self.start_bot()

        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️ درخواست توقف دریافت شد[/yellow]")
        except Exception as e:
            console.print(f"\n[red]❌ خطای غیرمنتظره: {str(e)}[/red]")
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    app = TelegramSenderApp()
    await app.run()


if __name__ == "__main__":
    try:
        # Run the application
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 خداحافظ![/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ خطای نهایی: {str(e)}[/red]")
        sys.exit(1)
