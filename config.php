<?php
/**
 * Configuration file for Telegram Sender Bot
 * راهنمای راه‌اندازی ربات ارسال کننده تلگرام
 */

// Bot Configuration / تنظیمات ربات
define('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE'); // Replace with your actual bot token from @BotFather
define('ADMIN_ID', 123456789); // Replace with your Telegram user ID

// File paths / مسیر فایل‌ها
define('ACCOUNTS_FILE', 'accounts.json');
define('MEMBERS_FILE', 'members.json');
define('LOGS_FILE', 'bot_logs.txt');

// Bot settings / تنظیمات ربات
define('MAX_ACCOUNTS', 100); // Maximum number of accounts
define('MESSAGE_DELAY', 500000); // Delay between messages in microseconds (0.5 seconds)
define('MAX_RETRIES', 3); // Maximum retry attempts for failed operations

/**
 * Setup Instructions / راهنمای راه‌اندازی:
 * 
 * 1. Create a new bot with @BotFather on Telegram
 *    یک ربات جدید با @BotFather در تلگرام بسازید
 * 
 * 2. Get your bot token and replace BOT_TOKEN above
 *    توکن ربات خود را دریافت کرده و در بالا جایگزین کنید
 * 
 * 3. Get your Telegram user ID and replace ADMIN_ID above
 *    شناسه کاربری تلگرام خود را دریافت کرده و در بالا جایگزین کنید
 *    You can get it from @userinfobot
 * 
 * 4. Upload files to your web server
 *    فایل‌ها را روی سرور وب خود آپلود کنید
 * 
 * 5. Set webhook URL (replace YOUR_DOMAIN with your actual domain):
 *    آدرس webhook را تنظیم کنید:
 *    https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://YOUR_DOMAIN/telegram_sender_bot.php
 * 
 * 6. Make sure your server supports:
 *    مطمئن شوید سرور شما از موارد زیر پشتیبانی کند:
 *    - PHP 7.0+
 *    - JSON extension
 *    - file_get_contents() with HTTPS
 *    - Write permissions for data files
 */

// Security check / بررسی امنیتی
if (BOT_TOKEN === 'YOUR_BOT_TOKEN_HERE' || ADMIN_ID === 123456789) {
    die('❌ Please configure BOT_TOKEN and ADMIN_ID in config.php first!');
}

// Utility functions / توابع کمکی

function logMessage($message) {
    $timestamp = date('Y-m-d H:i:s');
    $log_entry = "[{$timestamp}] {$message}\n";
    file_put_contents(LOGS_FILE, $log_entry, FILE_APPEND | LOCK_EX);
}

function isValidPhoneNumber($phone) {
    return preg_match('/^\+?[0-9]{10,15}$/', $phone);
}

function isValidGroupId($group_id) {
    return preg_match('/^-100[0-9]+$/', $group_id);
}

function formatBytes($size, $precision = 2) {
    $base = log($size, 1024);
    $suffixes = ['B', 'KB', 'MB', 'GB', 'TB'];
    return round(pow(1024, $base - floor($base)), $precision) . ' ' . $suffixes[floor($base)];
}

function getSystemStatus() {
    $status = [
        'php_version' => PHP_VERSION,
        'memory_usage' => memory_get_usage(true),
        'memory_limit' => ini_get('memory_limit'),
        'accounts_file_exists' => file_exists(ACCOUNTS_FILE),
        'members_file_exists' => file_exists(MEMBERS_FILE),
        'logs_file_exists' => file_exists(LOGS_FILE)
    ];
    
    return $status;
}

// Error handling / مدیریت خطاها
function handleError($errno, $errstr, $errfile, $errline) {
    $error_message = "Error [{$errno}]: {$errstr} in {$errfile} on line {$errline}";
    logMessage($error_message);
    return true;
}

set_error_handler('handleError');
?>