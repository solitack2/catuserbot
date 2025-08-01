# ربات ارسال کننده تلگرام / Telegram Sender Bot

یک ربات قدرتمند PHP برای مدیریت اکانت‌ها و ارسال پیام‌های انبوه در تلگرام

A powerful PHP bot for managing accounts and sending bulk messages on Telegram

## 🚀 قابلیت‌های اصلی / Main Features

### ✅ مدیریت اکانت‌ها / Account Management
- افزودن اکانت‌های جدید / Add new accounts
- بررسی وضعیت اکانت‌ها (سالم، محدود، بن، آفلاین) / Check account status (healthy, limited, banned, offline)
- نمایش آمار کامل اکانت‌ها / Display complete account statistics

### 🔍 انالیز پیشرفته گروه‌ها / Advanced Group Analysis
- استخراج لیست ممبرهای گروه از طریق تحلیل پیام‌ها / Extract group member lists through message analysis
- ذخیره اطلاعات ممبرها با جزئیات کامل / Save member information with complete details
- تاریخ‌گذاری و ردیابی انالیزها / Date stamping and analysis tracking

### 📨 ارسال پیام خصوصی / Private Messaging
- ارسال پیام‌های انبوه به ممبرهای استخراج شده / Send bulk messages to extracted members
- گزارش دقیق از وضعیت ارسال‌ها / Detailed delivery status reports
- کنترل سرعت ارسال برای جلوگیری از محدودیت / Rate limiting to avoid restrictions

## 📁 ساختار فایل‌ها / File Structure

```
telegram-sender-bot/
├── telegram_sender_bot.php    # فایل اصلی ربات / Main bot file
├── config.php                 # فایل تنظیمات / Configuration file
├── accounts.json              # ذخیره اکانت‌ها / Accounts storage
├── members.json               # ذخیره ممبرها / Members storage
├── bot_logs.txt              # لاگ‌های ربات / Bot logs
└── README.md                 # راهنمای استفاده / Usage guide
```

## ⚙️ راه‌اندازی / Setup

### 1. ایجاد ربات در تلگرام / Create Telegram Bot

1. به [@BotFather](https://t.me/BotFather) در تلگرام پیام دهید
2. دستور `/newbot` را ارسال کنید
3. نام و یوزرنیم ربات را انتخاب کنید
4. توکن ربات را کپی کنید

Send message to [@BotFather](https://t.me/BotFather) on Telegram:
1. Send `/newbot` command
2. Choose bot name and username
3. Copy the bot token

### 2. دریافت شناسه کاربری / Get User ID

1. به [@userinfobot](https://t.me/userinfobot) پیام دهید
2. شناسه عددی خود را کپی کنید

Send message to [@userinfobot](https://t.me/userinfobot) and copy your numeric user ID

### 3. تنظیم فایل‌ها / Configure Files

فایل `config.php` را ویرایش کنید / Edit `config.php` file:

```php
define('BOT_TOKEN', 'YOUR_ACTUAL_BOT_TOKEN');
define('ADMIN_ID', YOUR_ACTUAL_USER_ID);
```

### 4. آپلود به سرور / Upload to Server

فایل‌ها را در پوشه‌ای روی سرور وب خود قرار دهید که از طریق HTTPS قابل دسترسی باشد

Upload files to a web server directory accessible via HTTPS

### 5. تنظیم Webhook

آدرس زیر را در مرورگر باز کنید (با جایگزینی مقادیر مناسب):

Open this URL in browser (replace with your values):

```
https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://YOUR_DOMAIN/telegram_sender_bot.php
```

### 6. بررسی سیستم / System Requirements

مطمئن شوید سرور شما دارای موارد زیر است:

Ensure your server has:

- PHP 7.0 یا بالاتر / PHP 7.0+
- پسوند JSON فعال / JSON extension enabled
- دسترسی به `file_get_contents()` با HTTPS / HTTPS support for `file_get_contents()`
- مجوز نوشتن فایل / Write permissions for data files

## 📖 نحوه استفاده / Usage Guide

### شروع کار / Getting Started

1. ربات را در تلگرام پیدا کنید و `/start` بزنید
2. از منوی کیبورد گزینه مورد نظر را انتخاب کنید

Find your bot on Telegram and send `/start`, then use the keyboard menu

### افزودن اکانت / Adding Accounts

1. گزینه "➕ افزودن اکانت" را انتخاب کنید
2. شماره تلفن را وارد کنید (مثال: `+989123456789`)

Select "➕ افزودن اکانت" and enter phone number (example: `+989123456789`)

### بررسی وضعیت اکانت‌ها / Check Account Status

گزینه "📊 وضعیت اکانت‌ها" را انتخاب کنید تا آمار کامل مشاهده کنید:

Select "📊 وضعیت اکانت‌ها" to view complete statistics:

- ✅ سالم / Healthy
- ⚠️ محدود / Limited  
- ❌ بن / Banned
- ⭕ آفلاین / Offline

### انالیز گروه / Group Analysis

1. گزینه "🔍 انالیز گروه" را انتخاب کنید
2. شناسه گروه را وارد کنید (مثال: `-1001234567890`)

Select "🔍 انالیز گروه" and enter group ID (example: `-1001234567890`)

### مشاهده لیست ممبرها / View Member Lists

گزینه "👥 لیست ممبرها" را انتخاب کنید تا تمام ممبرهای استخراج شده را ببینید

Select "👥 لیست ممبرها" to view all extracted members

### ارسال پیام خصوصی / Send Private Messages

فرمت: `send:group_id:پیام شما`

Format: `send:group_id:your_message`

مثال / Example:
```
send:-1001234567890:سلام! این یک پیام تبلیغاتی است
```

## 🔧 تنظیمات پیشرفته / Advanced Configuration

### فایل config.php

```php
define('MAX_ACCOUNTS', 100);        // حداکثر تعداد اکانت
define('MESSAGE_DELAY', 500000);    // تاخیر بین پیام‌ها (میکروثانیه)
define('MAX_RETRIES', 3);           // حداکثر تلاش مجدد
```

### لاگ‌ها / Logs

تمام فعالیت‌ها در فایل `bot_logs.txt` ثبت می‌شوند

All activities are logged in `bot_logs.txt`

## ⚠️ نکات امنیتی / Security Notes

1. هرگز توکن ربات خود را به اشتراک نگذارید / Never share your bot token
2. فقط به ادمین مجاز دسترسی دهید / Only give access to authorized admin
3. فایل‌های حساس را از دسترسی عمومی محافظت کنید / Protect sensitive files from public access
4. به‌طور منظم فایل‌های لاگ را بررسی کنید / Regularly check log files

## 🐛 عیب‌یابی / Troubleshooting

### مشکلات رایج / Common Issues

1. **ربات پاسخ نمی‌دهد / Bot not responding:**
   - توکن و webhook را بررسی کنید / Check token and webhook
   - لاگ‌های سرور را مطالعه کنید / Check server logs

2. **خطای مجوز فایل / File permission error:**
   - مجوز نوشتن فایل‌ها را بررسی کنید / Check file write permissions
   - مالکیت فایل‌ها را تنظیم کنید / Set proper file ownership

3. **خطای JSON / JSON error:**
   - پسوند JSON در PHP فعال باشد / Ensure JSON extension is enabled
   - ساختار فایل‌های JSON را بررسی کنید / Validate JSON file structure

## 📞 پشتیبانی / Support

برای گزارش باگ یا پیشنهادات بهبود، لطفاً issue جدید ایجاد کنید

For bug reports or feature requests, please create a new issue

## 📄 مجوز / License

این پروژه تحت مجوز MIT منتشر شده است

This project is released under the MIT License

---

**تاریخ آخرین بروزرسانی / Last Updated:** 2024

**نسخه / Version:** 1.0.0
