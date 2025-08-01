# 🤖 ربات پیشرفته ارسال پیام تلگرام
# Advanced Telegram Private Message Sender Bot

## 🌟 ویژگی‌ها | Features

### فارسی
- 📱 **مدیریت چندین اکانت**: افزودن و مدیریت اکانت‌های متعدد تلگرام
- 📊 **آنالیز پیشرفته**: استخراج لیست ممبرهای گروه‌ها و کانال‌ها
- 📤 **ارسال پیام خصوصی**: ارسال پیام متنی و رسانه به پیوی کاربران
- 🏷️ **دسته‌بندی اکانت‌ها**: سازماندهی اکانت‌ها در دسته‌های مختلف
- 🌐 **پشتیبانی پروکسی**: استفاده از پروکسی برای اکانت‌ها
- ⚙️ **تنظیمات پیشرفته**: کنترل سرعت ارسال و زمان استراحت
- 🔢 **توزیع هش**: توزیع عددی روی اکانت‌ها
- 📈 **آمار و گزارش**: نمایش آمار کامل ارسال‌ها

### English
- 📱 **Multi-Account Management**: Add and manage multiple Telegram accounts
- 📊 **Advanced Analysis**: Extract member lists from groups and channels
- 📤 **Private Messaging**: Send text and media messages to users' DMs
- 🏷️ **Account Categories**: Organize accounts into different categories
- 🌐 **Proxy Support**: Use proxies for accounts
- ⚙️ **Advanced Settings**: Control sending speed and rest intervals
- 🔢 **Hash Distribution**: Distribute numbers across accounts
- 📈 **Statistics & Reports**: Complete sending statistics

## 🚀 نصب و راه‌اندازی | Installation & Setup

### پیش‌نیازها | Prerequisites
```bash
Python 3.8+
pip
```

### 1. کلون کردن پروژه | Clone Repository
```bash
git clone <repository-url>
cd telegram_sender_bot
```

### 2. نصب کتابخانه‌ها | Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. تنظیمات | Configuration
```bash
# کپی کردن فایل نمونه
cp .env.example .env

# ویرایش فایل .env
nano .env
```

### 4. دریافت BOT_TOKEN
1. به [@BotFather](https://t.me/BotFather) پیام دهید
2. دستور `/newbot` را ارسال کنید
3. نام و یوزرنیم ربات را تنظیم کنید
4. TOKEN دریافتی را در فایل `.env` قرار دهید

### 5. دریافت OWNER_ID
1. به [@userinfobot](https://t.me/userinfobot) پیام دهید
2. آیدی عددی خود را کپی کنید
3. در فایل `.env` قرار دهید

## 🎯 راه‌اندازی | Usage

### اجرای ربات | Run Bot
```bash
python main.py
```

### اجرای با Docker | Run with Docker
```bash
docker-compose up -d
```

## 📋 راهنمای استفاده | User Guide

### 1. افزودن اکانت | Add Account
- از [@BotFather](https://t.me/BotFather) BOT_TOKEN دریافت کنید
- از [my.telegram.org](https://my.telegram.org) API_ID و API_HASH دریافت کنید
- در ربات از منوی "📱 مدیریت اکانت‌ها" استفاده کنید

### 2. ایجاد دسته‌بندی | Create Categories
- از منوی "🏷️ ایجاد دسته‌بندی" استفاده کنید
- اکانت‌ها را به دسته‌های مختلف تخصیص دهید

### 3. آنالیز ممبرها | Analyze Members
- از منوی "📊 آنالیز پیشرفته" استفاده کنید
- اکانت مورد نظر را انتخاب کنید
- لینک گروه یا کانال را ارسال کنید

### 4. ارسال پیام | Send Messages
- از منوی "📤 ارسال به پیوی" استفاده کنید
- دسته‌بندی مورد نظر را انتخاب کنید
- لیست آیدی ممبرها را ارسال کنید
- پیام یا رسانه خود را ارسال کنید

### 5. تنظیمات | Settings
- تعداد ارسال در هر جلسه
- زمان استراحت بین ارسال‌ها
- تنظیمات پروکسی
- توزیع هش روی اکانت‌ها

## 🌐 مدیریت پروکسی | Proxy Management

### افزودن پروکسی | Add Proxy
```
Type: socks5/http
Host: proxy.example.com
Port: 1080
Username: (optional)
Password: (optional)
```

### تخصیص خودکار | Auto Assignment
ربات به صورت خودکار اکانت‌ها را به پروکسی‌های موجود تخصیص می‌دهد.

## 📊 آمار و گزارش | Statistics & Reports

- 📈 آمار روزانه ارسال
- 👥 وضعیت اکانت‌ها
- 🎯 نرخ موفقیت
- 📱 آمار هر اکانت
- 🏷️ آمار دسته‌بندی‌ها

## 🔧 تنظیمات پیشرفته | Advanced Configuration

### فایل config.py
```python
DEFAULT_SEND_LIMIT = 20  # پیام در هر جلسه
DEFAULT_DELAY_MIN = 30   # حداقل تاخیر (ثانیه)
DEFAULT_DELAY_MAX = 60   # حداکثر تاخیر (ثانیه)
DEFAULT_ACCOUNT_REST = 300  # استراحت اکانت (ثانیه)
```

### متغیرهای محیطی | Environment Variables
```bash
BOT_TOKEN=your_bot_token
OWNER_ID=your_user_id
DEFAULT_SEND_LIMIT=20
DEFAULT_DELAY_MIN=30
DEFAULT_DELAY_MAX=60
```

## 🚨 نکات مهم | Important Notes

### امنیت | Security
- هرگز TOKEN ربات را با دیگران به اشتراک نگذارید
- از پروکسی معتبر استفاده کنید
- فایل‌های session را محافظت کنید

### محدودیت‌ها | Limitations
- رعایت قوانین تلگرام الزامی است
- از flood wait جلوگیری کنید
- تعداد ارسال روزانه را محدود کنید

### خطاها | Troubleshooting
- لاگ‌ها در پوشه `logs` ذخیره می‌شوند
- در صورت خطا، لاگ‌ها را بررسی کنید
- برای مشکلات proxy، اتصال را بررسی کنید

## 📁 ساختار پروژه | Project Structure

```
telegram_sender_bot/
├── main.py              # فایل اصلی
├── bot.py               # منطق ربات
├── sender.py            # سیستم ارسال
├── database.py          # مدیریت دیتابیس
├── config.py            # تنظیمات
├── requirements.txt     # کتابخانه‌ها
├── .env.example         # نمونه تنظیمات
├── sessions/            # فایل‌های session
├── media/               # فایل‌های رسانه
└── logs/                # لاگ‌ها
```

## 🤝 مشارکت | Contributing

1. پروژه را Fork کنید
2. برنچ جدید بسازید (`git checkout -b feature/AmazingFeature`)
3. تغییرات را Commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. به برنچ Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request باز کنید

## 📄 مجوز | License

این پروژه تحت مجوز MIT منتشر شده است. فایل [LICENSE](LICENSE) را برای جزئیات بیشتر مطالعه کنید.

## 📞 پشتیبانی | Support

- 🐛 گزارش باگ: [Issues](../../issues)
- 💡 درخواست ویژگی: [Feature Requests](../../issues)
- 📖 مستندات: [Wiki](../../wiki)

## ⚠️ اخلاق و قانون | Ethics & Legal

این ابزار صرفاً برای اهداف آموزشی و مشروع طراحی شده است. کاربران مسئول رعایت قوانین محلی و شرایط استفاده تلگرام هستند.

---

**نکته**: این ربات به منظور آموزش و استفاده مشروع طراحی شده است. لطفاً از آن سوءاستفاده نکنید.

**Note**: This bot is designed for educational and legitimate purposes. Please do not misuse it.
