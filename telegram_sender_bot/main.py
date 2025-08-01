#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Telegram Private Message Sender Bot
============================================

A comprehensive Telegram bot for managing multiple accounts and sending private messages
with advanced analytics, flood control, and user management features.

Author: AI Assistant
Version: 1.0.0
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

from analytics import AdvancedAnalytics
from bot import TelegramBot
from sender import TelegramSender

console = Console()


class TelegramSenderApp:
    def __init__(self):
        self.bot = None
        self.sender = None
        self.analytics = None
        self.running = False

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            console.print("\n[yellow]🛑 Shutting down gracefully...[/yellow]")
            self.running = False
            if self.sender:
                asyncio.create_task(self.sender.close_all())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def display_banner(self):
        """Display application banner"""
        banner_text = """
╔══════════════════════════════════════════════╗
║     🚀 Advanced Telegram Sender Bot 🚀      ║
║                                              ║
║  📱 Multi-Account Management                 ║
║  📤 Private Message Sending                 ║
║  📊 Advanced Analytics                       ║
║  🔄 Bulk Messaging with Flood Control       ║
║  📋 Message Templates                        ║
║  🔍 User Search & Discovery                  ║
╚══════════════════════════════════════════════╝
        """

        console.print(
            Panel(
                banner_text,
                title="[bold blue]Telegram Sender Bot[/bold blue]",
                border_style="blue",
            )
        )

    def check_configuration(self):
        """Check if all required configurations are set"""
        missing_configs = []

        if not Config.BOT_TOKEN:
            missing_configs.append("BOT_TOKEN")
        if not Config.OWNER_ID:
            missing_configs.append("OWNER_ID")

        if missing_configs:
            console.print("[red]❌ Missing required configuration:[/red]")
            for config in missing_configs:
                console.print(f"   • {config}")
            console.print("\n[yellow]Please set these in your .env file[/yellow]")
            return False

        return True

    def display_config_info(self):
        """Display current configuration"""
        table = Table(title="📋 Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Bot Token", f"{'✅ Set' if Config.BOT_TOKEN else '❌ Not Set'}")
        table.add_row(
            "Owner ID", str(Config.OWNER_ID) if Config.OWNER_ID else "❌ Not Set"
        )
        table.add_row("Max Messages/Min", str(Config.MAX_MESSAGES_PER_MINUTE))
        table.add_row("Message Delay", f"{Config.DELAY_BETWEEN_MESSAGES}s")
        table.add_row(
            "Analytics", "✅ Enabled" if Config.ENABLE_ANALYTICS else "❌ Disabled"
        )
        table.add_row(
            "Flood Control",
            "✅ Enabled" if Config.ENABLE_FLOOD_CONTROL else "❌ Disabled",
        )

        console.print(table)

    async def initialize_components(self):
        """Initialize all application components"""
        try:
            console.print("[yellow]🔄 Initializing components...[/yellow]")

            # Initialize sender
            self.sender = TelegramSender()
            console.print("[green]✅ Sender initialized[/green]")

            # Initialize analytics
            if Config.ENABLE_ANALYTICS:
                self.analytics = AdvancedAnalytics()
                console.print("[green]✅ Analytics initialized[/green]")

            # Load existing accounts
            await self.sender.load_accounts()
            accounts = self.sender.get_accounts_list()
            console.print(f"[green]✅ Loaded {len(accounts)} accounts[/green]")

            # Initialize bot
            self.bot = TelegramBot()
            console.print("[green]✅ Bot initialized[/green]")

            return True

        except Exception as e:
            console.print(f"[red]❌ Error initializing components: {str(e)}[/red]")
            return False

    def display_accounts_summary(self):
        """Display summary of loaded accounts"""
        if not self.sender:
            return

        accounts = self.sender.get_accounts_list()

        if not accounts:
            console.print(
                "[yellow]📱 No accounts found. Add accounts using the bot.[/yellow]"
            )
            return

        table = Table(title="📱 Loaded Accounts")
        table.add_column("Phone", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Username", style="blue")
        table.add_column("Status", style="yellow")
        table.add_column("Total Sent", style="magenta")

        for account in accounts:
            status = "🟢 Active" if account["is_active"] else "🔴 Inactive"
            name = f"{account['first_name'] or ''} {account['last_name'] or ''}".strip()
            username = f"@{account['username']}" if account["username"] else "None"

            table.add_row(
                account["phone"],
                name or "Unknown",
                username,
                status,
                str(account["total_sent"]),
            )

        console.print(table)

    def display_analytics_summary(self):
        """Display analytics summary"""
        if not self.analytics:
            return

        try:
            report = self.analytics.get_performance_report(7)
            console.print(
                Panel(
                    report,
                    title="[bold green]📊 Performance Summary[/bold green]",
                    border_style="green",
                )
            )

            recommendations = self.analytics.get_recommendations()
            if recommendations:
                rec_text = "\n".join(recommendations)
                console.print(
                    Panel(
                        rec_text,
                        title="[bold yellow]💡 Recommendations[/bold yellow]",
                        border_style="yellow",
                    )
                )
        except Exception as e:
            console.print(f"[red]❌ Error displaying analytics: {str(e)}[/red]")

    def display_usage_instructions(self):
        """Display usage instructions"""
        instructions = """
🔧 **Getting Started:**

1. Make sure you have set BOT_TOKEN and OWNER_ID in your .env file
2. Start the bot and send /start command
3. Add your Telegram accounts using the bot interface
4. Start sending private messages!

🎯 **Bot Commands:**
• /start - Show main menu
• Use inline keyboards for navigation

📱 **Adding Accounts:**
• Get API credentials from https://my.telegram.org
• Use bot interface to add accounts step by step

📤 **Sending Messages:**
• Single messages to specific users
• Bulk messaging with flood protection
• Use message templates for efficiency

📊 **Analytics:**
• View real-time statistics
• Generate performance charts
• Get improvement recommendations
        """

        console.print(
            Panel(
                instructions,
                title="[bold blue]📖 Usage Instructions[/bold blue]",
                border_style="blue",
            )
        )

    async def run(self):
        """Main application entry point"""
        self.setup_signal_handlers()
        self.display_banner()

        # Check configuration
        if not self.check_configuration():
            return

        self.display_config_info()

        # Initialize components
        if not await self.initialize_components():
            return

        # Display summaries
        self.display_accounts_summary()

        if Config.ENABLE_ANALYTICS:
            self.display_analytics_summary()

        self.display_usage_instructions()

        # Start the bot
        console.print("\n[bold green]🚀 Starting Telegram Bot...[/bold green]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

        try:
            self.running = True
            self.bot.run()
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Goodbye![/yellow]")
        except Exception as e:
            console.print(f"\n[red]❌ Error running bot: {str(e)}[/red]")
        finally:
            if self.sender:
                await self.sender.close_all()


def main():
    """Main function"""
    # Create necessary directories
    os.makedirs("sessions", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(
                """# Copy this file to .env and fill in your values
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_telegram_user_id

# Optional settings
API_ID=your_api_id
API_HASH=your_api_hash
LOG_LEVEL=INFO
"""
            )
        console.print(
            "[yellow]📝 Created .env file. Please fill in your configuration.[/yellow]"
        )
        return

    # Run the application
    app = TelegramSenderApp()

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Application stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Fatal error: {str(e)}[/red]")
        logging.exception("Fatal error occurred")


if __name__ == "__main__":
    main()
