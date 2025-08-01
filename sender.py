import asyncio
import logging
import random
import os
from typing import Dict, List, Optional, Any
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserPrivacyRestricted, PeerIdInvalid, SessionPasswordNeeded
from pyrogram.types import User, Chat, ChatMember
import time
from datetime import datetime, timedelta
from database import DatabaseManager
from config import Config

class TelegramSender:
    def __init__(self):
        self.db = DatabaseManager()
        self.clients: Dict[int, Client] = {}  # account_id -> client
        self.proxy_clients: Dict[str, List[int]] = {}  # proxy_host -> [account_ids]
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging for sender"""
        logger = logging.getLogger('telegram_sender')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(os.path.join(Config.LOGS_DIR, 'sender.log'))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def add_account(self, phone: str, api_id: int, api_hash: str) -> bool:
        """Add new account with automatic proxy assignment"""
        try:
            session_name = phone.replace('+', '')
            session_path = os.path.join(Config.SESSIONS_DIR, session_name)
            
            # Get available proxy
            proxy = self.db.get_available_proxy()
            proxy_dict = None
            
            if proxy:
                proxy_dict = {
                    "scheme": proxy['type'],
                    "hostname": proxy['host'],
                    "port": proxy['port']
                }
                if proxy.get('username'):
                    proxy_dict["username"] = proxy['username']
                    proxy_dict["password"] = proxy['password']
            
            # Create client
            client = Client(
                session_path,
                api_id=api_id,
                api_hash=api_hash,
                phone_number=phone,
                proxy=proxy_dict
            )
            
            # Test connection
            await client.start()
            me = await client.get_me()
            await client.stop()
            
            self.logger.info(f"Account {phone} added successfully")
            return True
            
        except SessionPasswordNeeded:
            self.logger.error(f"Account {phone} requires 2FA password")
            return False
        except Exception as e:
            self.logger.error(f"Error adding account {phone}: {str(e)}")
            return False
    
    async def load_account(self, account: Dict) -> Optional[Client]:
        """Load single account with proxy support"""
        try:
            session_name = account['phone'].replace('+', '')
            session_path = os.path.join(Config.SESSIONS_DIR, session_name)
            
            # Setup proxy if assigned
            proxy_dict = None
            if account.get('proxy_id'):
                proxies = self.db.get_proxies()
                proxy = next((p for p in proxies if p['id'] == account['proxy_id']), None)
                if proxy and proxy['is_active']:
                    proxy_dict = {
                        "scheme": proxy['type'],
                        "hostname": proxy['host'],
                        "port": proxy['port']
                    }
                    if proxy.get('username'):
                        proxy_dict["username"] = proxy['username']
                        proxy_dict["password"] = proxy['password']
            
            # Create client
            client = Client(
                session_path,
                api_id=account['api_id'],
                api_hash=account['api_hash'],
                proxy=proxy_dict
            )
            
            # Test connection
            await client.start()
            
            # Update account status
            me = await client.get_me()
            self.db.update_account_status(account['id'], 'active')
            
            # Store client
            self.clients[account['id']] = client
            
            self.logger.info(f"Account {account['phone']} loaded successfully")
            return client
            
        except FloodWait as fw:
            wait_until = datetime.now() + timedelta(seconds=fw.value)
            self.db.update_account_status(account['id'], 'flood', f"Flood wait until {wait_until}")
            self.logger.warning(f"Account {account['phone']} flood wait: {fw.value}s")
            return None
            
        except Exception as e:
            self.db.update_account_status(account['id'], 'error', str(e))
            self.logger.error(f"Error loading account {account['phone']}: {str(e)}")
            return None
    
    async def load_category_accounts(self, category_id: int) -> List[Client]:
        """Load all accounts from a category"""
        accounts = self.db.get_accounts(category_id)
        loaded_clients = []
        
        for account in accounts:
            if account['status'] in ['active', 'error']:  # Skip flood wait accounts
                client = await self.load_account(account)
                if client:
                    loaded_clients.append(client)
        
        return loaded_clients
    
    async def extract_members(self, account_id: int, chat_identifier: str) -> List[Dict]:
        """Extract members from chat using specified account"""
        try:
            # Load account if not already loaded
            if account_id not in self.clients:
                account = next((acc for acc in self.db.get_accounts() if acc['id'] == account_id), None)
                if not account:
                    raise Exception("Account not found")
                
                client = await self.load_account(account)
                if not client:
                    raise Exception("Failed to load account")
            else:
                client = self.clients[account_id]
            
            # Get chat
            if chat_identifier.startswith('@'):
                chat = await client.get_chat(chat_identifier)
            elif chat_identifier.startswith('https://t.me/'):
                username = chat_identifier.split('/')[-1]
                chat = await client.get_chat(username)
            else:
                chat = await client.get_chat(int(chat_identifier))
            
            members = []
            batch_count = 0
            
            # Extract members in batches
            async for member in client.get_chat_members(chat.id):
                if isinstance(member, ChatMember) and member.user:
                    user_data = {
                        'id': member.user.id,
                        'username': member.user.username,
                        'first_name': member.user.first_name,
                        'last_name': member.user.last_name,
                        'phone': getattr(member.user, 'phone_number', None),
                        'chat_id': chat.id,
                        'chat_title': chat.title
                    }
                    members.append(user_data)
                    
                    batch_count += 1
                    if batch_count >= Config.ANALYSIS_BATCH_SIZE:
                        await asyncio.sleep(Config.ANALYSIS_DELAY)
                        batch_count = 0
            
            self.logger.info(f"Extracted {len(members)} members from {chat_identifier}")
            return members
            
        except FloodWait as fw:
            self.logger.warning(f"Flood wait during extraction: {fw.value}s")
            await asyncio.sleep(fw.value)
            return []
            
        except Exception as e:
            self.logger.error(f"Error extracting members: {str(e)}")
            raise e
    
    async def send_message(self, client: Client, user_id: int, message: str, media_path: str = None) -> Dict:
        """Send single message to user"""
        try:
            if media_path and os.path.exists(media_path):
                # Send media message
                if media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    await client.send_photo(user_id, media_path, caption=message)
                elif media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    await client.send_video(user_id, media_path, caption=message)
                else:
                    await client.send_document(user_id, media_path, caption=message)
            else:
                # Send text message
                await client.send_message(user_id, message)
            
            return {'status': 'success', 'user_id': user_id}
            
        except UserPrivacyRestricted:
            return {'status': 'failed', 'user_id': user_id, 'error': 'User privacy restricted'}
        except PeerIdInvalid:
            return {'status': 'failed', 'user_id': user_id, 'error': 'Invalid peer ID'}
        except FloodWait as fw:
            return {'status': 'flood_wait', 'user_id': user_id, 'wait_time': fw.value}
        except Exception as e:
            return {'status': 'failed', 'user_id': user_id, 'error': str(e)}
    
    async def send_bulk_messages(self, category_id: int, member_ids: List[int], 
                                message: str, media_path: str = None) -> List[Dict]:
        """Send bulk messages using category accounts"""
        try:
            # Load accounts from category
            clients = await self.load_category_accounts(category_id)
            if not clients:
                raise Exception("No active accounts in category")
            
            # Get settings
            settings = self.db.get_all_settings()
            send_limit = int(settings.get('send_limit', Config.DEFAULT_SEND_LIMIT))
            delay_min = int(settings.get('delay_min', Config.DEFAULT_DELAY_MIN))
            delay_max = int(settings.get('delay_max', Config.DEFAULT_DELAY_MAX))
            account_rest = int(settings.get('account_rest', Config.DEFAULT_ACCOUNT_REST))
            
            results = []
            current_client_idx = 0
            messages_sent_per_client = {i: 0 for i in range(len(clients))}
            
            for member_id in member_ids:
                # Check if current client reached limit
                if messages_sent_per_client[current_client_idx] >= send_limit:
                    # Find next available client
                    next_client_idx = None
                    for i in range(len(clients)):
                        if messages_sent_per_client[i] < send_limit:
                            next_client_idx = i
                            break
                    
                    if next_client_idx is None:
                        # All clients reached limit
                        self.logger.info("All accounts reached sending limit")
                        break
                    
                    current_client_idx = next_client_idx
                
                # Send message
                client = clients[current_client_idx]
                result = await self.send_message(client, member_id, message, media_path)
                results.append(result)
                
                # Log to database
                account_id = list(self.clients.keys())[list(self.clients.values()).index(client)]
                status = 'sent' if result['status'] == 'success' else 'failed'
                self.db.log_message(account_id, member_id, message, status, category_id, media_path)
                
                # Handle flood wait
                if result['status'] == 'flood_wait':
                    self.logger.warning(f"Flood wait: {result['wait_time']}s")
                    await asyncio.sleep(result['wait_time'])
                
                # Update counters
                if result['status'] == 'success':
                    messages_sent_per_client[current_client_idx] += 1
                
                # Random delay between messages
                delay = random.randint(delay_min, delay_max)
                await asyncio.sleep(delay)
                
                # Check if client needs rest
                if messages_sent_per_client[current_client_idx] >= send_limit:
                    self.logger.info(f"Account reached limit, resting for {account_rest}s")
                    # Move to next client
                    current_client_idx = (current_client_idx + 1) % len(clients)
            
            self.logger.info(f"Bulk sending completed: {len(results)} messages processed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in bulk sending: {str(e)}")
            raise e
    
    async def distribute_hash_on_accounts(self, hash_count: int) -> Dict[str, Any]:
        """Distribute hash/numbers across accounts"""
        try:
            accounts = self.db.get_accounts()
            if not accounts:
                return {'success': False, 'error': 'No accounts available'}
            
            # Calculate distribution
            accounts_per_hash = max(1, len(accounts) // hash_count)
            distribution = {}
            
            for i in range(hash_count):
                start_idx = i * accounts_per_hash
                end_idx = min((i + 1) * accounts_per_hash, len(accounts))
                
                hash_accounts = accounts[start_idx:end_idx]
                distribution[f"hash_{i+1}"] = [
                    {
                        'id': acc['id'],
                        'phone': acc['phone'],
                        'name': acc['first_name'] or acc['phone']
                    }
                    for acc in hash_accounts
                ]
            
            # Handle remaining accounts
            remaining_start = hash_count * accounts_per_hash
            if remaining_start < len(accounts):
                remaining_accounts = accounts[remaining_start:]
                distribution["remaining"] = [
                    {
                        'id': acc['id'],
                        'phone': acc['phone'],
                        'name': acc['first_name'] or acc['phone']
                    }
                    for acc in remaining_accounts
                ]
            
            return {'success': True, 'distribution': distribution}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def auto_assign_proxies(self) -> Dict[str, Any]:
        """Automatically assign proxies to accounts"""
        try:
            accounts = self.db.get_accounts()
            proxies = self.db.get_proxies()
            
            if not proxies:
                return {'success': False, 'error': 'No proxies available'}
            
            assigned_count = 0
            
            for account in accounts:
                if not account.get('proxy_id'):
                    # Find available proxy
                    available_proxy = self.db.get_available_proxy()
                    if available_proxy:
                        self.db.assign_proxy_to_account(account['id'], available_proxy['id'])
                        assigned_count += 1
            
            return {
                'success': True, 
                'assigned_count': assigned_count,
                'total_accounts': len(accounts)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def check_account_status(self, account_id: int) -> Dict[str, Any]:
        """Check detailed account status"""
        try:
            account = next((acc for acc in self.db.get_accounts() if acc['id'] == account_id), None)
            if not account:
                return {'success': False, 'error': 'Account not found'}
            
            # Try to load account to check status
            client = await self.load_account(account)
            
            if client:
                try:
                    me = await client.get_me()
                    
                    # Check if premium
                    is_premium = getattr(me, 'is_premium', False)
                    
                    # Update database
                    if is_premium != account.get('is_premium', False):
                        # Update premium status in database
                        pass  # Would need to add this to database schema
                    
                    status_info = {
                        'success': True,
                        'status': 'active',
                        'user_info': {
                            'id': me.id,
                            'first_name': me.first_name,
                            'last_name': me.last_name,
                            'username': me.username,
                            'phone': me.phone_number,
                            'is_premium': is_premium,
                            'is_verified': getattr(me, 'is_verified', False)
                        }
                    }
                    
                    await client.stop()
                    return status_info
                    
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            else:
                return {'success': False, 'error': 'Failed to connect to account'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_account_analytics(self, account_id: int, days: int = 7) -> Dict[str, Any]:
        """Get analytics for specific account"""
        try:
            # Get account stats from database
            stats = self.db.get_account_stats()
            account_stat = next((stat for stat in stats if stat['id'] == account_id), None)
            
            if not account_stat:
                return {'success': False, 'error': 'Account not found'}
            
            # Calculate success rate
            total_messages = account_stat['total_messages']
            successful = account_stat['successful']
            success_rate = (successful / total_messages * 100) if total_messages > 0 else 0
            
            return {
                'success': True,
                'analytics': {
                    'total_messages': total_messages,
                    'successful_messages': successful,
                    'failed_messages': account_stat['failed'],
                    'success_rate': round(success_rate, 2),
                    'status': account_stat['status'],
                    'category': account_stat['category_name']
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def cleanup_clients(self):
        """Clean up all active clients"""
        for client in self.clients.values():
            try:
                if client.is_connected:
                    await client.stop()
            except:
                pass
        
        self.clients.clear()
        self.logger.info("All clients cleaned up")
    
    async def stop_all_tasks(self):
        """Stop all active tasks"""
        for task_name, task in self.active_tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"Cancelled task: {task_name}")
        
        self.active_tasks.clear()
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.cleanup_clients())
        except:
            pass