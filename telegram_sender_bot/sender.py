import asyncio
import logging
import os
import random
from typing import Dict, List

from config import Config
from pyrogram import Client, errors

from database import DatabaseManager


class TelegramSender:
    def __init__(self):
        self.db = DatabaseManager()
        self.clients = {}
        self.session_folder = Config.SESSION_FOLDER
        self.setup_logging()

        # Create sessions folder if not exists
        if not os.path.exists(self.session_folder):
            os.makedirs(self.session_folder)

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(Config.LOG_FILE, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    async def add_account(self, phone: str, api_id: int, api_hash: str) -> Dict:
        """Add new Telegram account"""
        try:
            session_name = f"session_{phone.replace('+', '')}"
            session_path = os.path.join(self.session_folder, session_name)

            # Create Pyrogram client
            client = Client(
                session_path, api_id=api_id, api_hash=api_hash, phone_number=phone
            )

            # Connect and authorize
            await client.start()

            # Get user info
            me = await client.get_me()

            # Save to database
            account_id = self.db.add_account(
                phone=phone,
                session_name=session_name,
                api_id=api_id,
                api_hash=api_hash,
                first_name=me.first_name,
                last_name=me.last_name,
                username=me.username,
            )

            # Store client
            self.clients[account_id] = client

            self.logger.info(f"Account added successfully: {phone}")
            return {
                "success": True,
                "account_id": account_id,
                "user_info": {
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "username": me.username,
                    "phone": phone,
                },
            }

        except errors.PhoneNumberInvalid:
            return {"success": False, "error": "شماره تلفن نامعتبر است"}
        except errors.PhoneCodeInvalid:
            return {"success": False, "error": "کد تایید نامعتبر است"}
        except errors.SessionPasswordNeeded:
            return {"success": False, "error": "رمز عبور دو مرحله‌ای مورد نیاز است"}
        except Exception as e:
            self.logger.error(f"Error adding account: {str(e)}")
            return {"success": False, "error": str(e)}

    async def load_accounts(self):
        """Load all active accounts"""
        accounts = self.db.get_accounts(active_only=True)

        for account in accounts:
            try:
                session_path = os.path.join(
                    self.session_folder, account["session_name"]
                )

                if os.path.exists(f"{session_path}.session"):
                    client = Client(
                        session_path,
                        api_id=account["api_id"],
                        api_hash=account["api_hash"],
                    )

                    await client.start()
                    self.clients[account["id"]] = client
                    self.logger.info(f"Loaded account: {account['phone']}")

            except Exception as e:
                self.logger.error(f"Error loading account {account['phone']}: {str(e)}")

    async def send_private_message(
        self,
        account_id: int,
        target_identifier: str,
        message: str,
        message_type: str = "text",
    ) -> Dict:
        """Send private message to user"""
        try:
            if account_id not in self.clients:
                return {"success": False, "error": "اکانت یافت نشد یا متصل نیست"}

            client = self.clients[account_id]

            # Resolve target user
            try:
                if target_identifier.isdigit():
                    target_user = await client.get_users(int(target_identifier))
                else:
                    target_user = await client.get_users(
                        target_identifier.replace("@", "")
                    )
            except Exception:
                return {"success": False, "error": "کاربر مقصد یافت نشد"}

            # Log message to database
            message_id = self.db.log_message(
                account_id=account_id,
                target_user_id=target_user.id,
                target_username=target_user.username or str(target_user.id),
                message_text=message,
                message_type=message_type,
            )

            # Send message
            if message_type == "text":
                sent_message = await client.send_message(target_user.id, message)
            elif message_type == "photo":
                # Assuming message contains photo path
                sent_message = await client.send_photo(target_user.id, message)
            elif message_type == "document":
                # Assuming message contains document path
                sent_message = await client.send_document(target_user.id, message)

            # Update message status
            self.db.update_message_status(message_id, "sent")
            self.db.update_account_usage(account_id)

            self.logger.info(
                f"Message sent to {target_user.username or target_user.id}"
            )

            # Add delay to prevent flood
            await asyncio.sleep(Config.DELAY_BETWEEN_MESSAGES)

            return {
                "success": True,
                "message_id": sent_message.id,
                "target_user": {
                    "id": target_user.id,
                    "username": target_user.username,
                    "first_name": target_user.first_name,
                },
            }

        except errors.PeerFlood:
            self.db.update_message_status(
                message_id, "failed", "محدودیت ارسال پیام (Flood)"
            )
            return {"success": False, "error": "محدودیت ارسال پیام. لطفا کمی صبر کنید"}
        except errors.UserIsBlocked:
            self.db.update_message_status(
                message_id, "failed", "کاربر شما را مسدود کرده"
            )
            return {"success": False, "error": "کاربر شما را مسدود کرده است"}
        except errors.ChatWriteForbidden:
            self.db.update_message_status(
                message_id, "failed", "امکان ارسال پیام وجود ندارد"
            )
            return {
                "success": False,
                "error": "امکان ارسال پیام به این کاربر وجود ندارد",
            }
        except Exception as e:
            self.db.update_message_status(message_id, "failed", str(e))
            self.logger.error(f"Error sending message: {str(e)}")
            return {"success": False, "error": str(e)}

    async def bulk_send(
        self,
        account_id: int,
        target_list: List[str],
        message: str,
        delay_range: tuple = (2, 5),
    ) -> Dict:
        """Send message to multiple users"""
        results = {
            "total": len(target_list),
            "successful": 0,
            "failed": 0,
            "details": [],
        }

        for target in target_list:
            try:
                result = await self.send_private_message(account_id, target, message)

                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1

                results["details"].append(
                    {
                        "target": target,
                        "success": result["success"],
                        "error": result.get("error"),
                    }
                )

                # Random delay between messages
                delay = random.uniform(delay_range[0], delay_range[1])
                await asyncio.sleep(delay)

            except Exception as e:
                results["failed"] += 1
                results["details"].append(
                    {"target": target, "success": False, "error": str(e)}
                )

        return results

    async def get_account_info(self, account_id: int) -> Dict:
        """Get account information"""
        try:
            if account_id not in self.clients:
                return {"success": False, "error": "اکانت یافت نشد"}

            client = self.clients[account_id]
            me = await client.get_me()

            return {
                "success": True,
                "info": {
                    "id": me.id,
                    "first_name": me.first_name,
                    "last_name": me.last_name,
                    "username": me.username,
                    "phone": me.phone_number,
                    "is_premium": me.is_premium,
                    "is_verified": me.is_verified,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_users(
        self, account_id: int, query: str, limit: int = 10
    ) -> List[Dict]:
        """Search for users"""
        try:
            if account_id not in self.clients:
                return []

            client = self.clients[account_id]
            users = []

            async for user in client.search_global(query, limit=limit):
                if hasattr(user, "first_name"):  # Is a user, not a chat
                    users.append(
                        {
                            "id": user.id,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "username": user.username,
                            "is_premium": getattr(user, "is_premium", False),
                        }
                    )

            return users
        except Exception as e:
            self.logger.error(f"Error searching users: {str(e)}")
            return []

    async def close_all(self):
        """Close all client connections"""
        for client in self.clients.values():
            try:
                await client.stop()
            except:
                pass
        self.clients.clear()

    def get_analytics(self, days: int = 7) -> Dict:
        """Get analytics data"""
        return self.db.get_analytics(days)

    def get_accounts_list(self) -> List[Dict]:
        """Get list of all accounts"""
        return self.db.get_accounts(active_only=False)
