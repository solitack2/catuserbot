<?php
require_once 'config.php';

class TelegramBot {
    private $botToken;
    private $adminId;
    private $db;
    
    public function __construct() {
        $this->botToken = BOT_TOKEN;
        $this->adminId = ADMIN_ID;
        $this->db = getDB();
    }
    
    // Send message to Telegram
    private function sendMessage($chatId, $text, $keyboard = null, $parseMode = 'HTML') {
        $url = "https://api.telegram.org/bot" . $this->botToken . "/sendMessage";
        $data = [
            'chat_id' => $chatId,
            'text' => $text,
            'parse_mode' => $parseMode
        ];
        
        if ($keyboard) {
            $data['reply_markup'] = json_encode($keyboard);
        }
        
        return $this->makeRequest($url, $data);
    }
    
    // Send video to Telegram
    private function sendVideo($chatId, $videoUrl, $caption = '') {
        $url = "https://api.telegram.org/bot" . $this->botToken . "/sendVideo";
        $data = [
            'chat_id' => $chatId,
            'video' => $videoUrl,
            'caption' => $caption,
            'parse_mode' => 'HTML'
        ];
        
        return $this->makeRequest($url, $data);
    }
    
    // Send document to Telegram
    private function sendDocument($chatId, $documentUrl, $caption = '') {
        $url = "https://api.telegram.org/bot" . $this->botToken . "/sendDocument";
        $data = [
            'chat_id' => $chatId,
            'document' => $documentUrl,
            'caption' => $caption,
            'parse_mode' => 'HTML'
        ];
        
        return $this->makeRequest($url, $data);
    }
    
    // Make HTTP request
    private function makeRequest($url, $data) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        
        $result = curl_exec($ch);
        curl_close($ch);
        
        return json_decode($result, true);
    }
    
    // Extract Instagram video URL
    private function getInstagramVideoUrl($url) {
        // Clean the URL
        $url = trim($url);
        if (strpos($url, 'instagram.com') === false) {
            return false;
        }
        
        // Add ?__a=1 parameter for JSON response
        if (strpos($url, '?') !== false) {
            $url .= '&__a=1';
        } else {
            $url .= '?__a=1';
        }
        
        try {
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $url);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
            curl_setopt($ch, CURLOPT_TIMEOUT, 30);
            
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            if ($httpCode === 200 && $response) {
                $data = json_decode($response, true);
                
                // Try different JSON structures
                if (isset($data['graphql']['shortcode_media']['video_url'])) {
                    return $data['graphql']['shortcode_media']['video_url'];
                }
                
                if (isset($data['items'][0]['video_versions'][0]['url'])) {
                    return $data['items'][0]['video_versions'][0]['url'];
                }
                
                // Alternative method using regex
                $originalUrl = str_replace(['?__a=1', '&__a=1'], '', $url);
                return $this->extractVideoUrlWithRegex($originalUrl);
            }
            
            return false;
        } catch (Exception $e) {
            error_log("Instagram download error: " . $e->getMessage());
            return false;
        }
    }
    
    // Alternative method using regex
    private function extractVideoUrlWithRegex($url) {
        try {
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $url);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
            
            $html = curl_exec($ch);
            curl_close($ch);
            
            // Extract video URL from HTML
            if (preg_match('/"video_url":"([^"]+)"/', $html, $matches)) {
                return str_replace('\u0026', '&', $matches[1]);
            }
            
            return false;
        } catch (Exception $e) {
            return false;
        }
    }
    
    // User management functions
    private function addUser($userId, $username, $firstName, $lastName) {
        try {
            $stmt = $this->db->prepare("INSERT INTO users (id, username, first_name, last_name) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE username=?, first_name=?, last_name=?, last_activity=NOW()");
            return $stmt->execute([$userId, $username, $firstName, $lastName, $username, $firstName, $lastName]);
        } catch (PDOException $e) {
            return false;
        }
    }
    
    private function getUser($userId) {
        try {
            $stmt = $this->db->prepare("SELECT * FROM users WHERE id = ?");
            $stmt->execute([$userId]);
            return $stmt->fetch(PDO::FETCH_ASSOC);
        } catch (PDOException $e) {
            return false;
        }
    }
    
    private function incrementDownloads($userId) {
        try {
            $stmt = $this->db->prepare("UPDATE users SET downloads_today = downloads_today + 1, total_downloads = total_downloads + 1 WHERE id = ?");
            return $stmt->execute([$userId]);
        } catch (PDOException $e) {
            return false;
        }
    }
    
    private function addDownloadRecord($userId, $url, $fileType, $fileSize) {
        try {
            $stmt = $this->db->prepare("INSERT INTO downloads (user_id, url, file_type, file_size) VALUES (?, ?, ?, ?)");
            return $stmt->execute([$userId, $url, $fileType, $fileSize]);
        } catch (PDOException $e) {
            return false;
        }
    }
    
    // Check if user can download (daily limit)
    private function canUserDownload($userId) {
        $user = $this->getUser($userId);
        return $user && $user['downloads_today'] < MAX_DOWNLOADS_PER_DAY && !$user['is_banned'];
    }
    
    // Get user statistics
    private function getUserStats($userId) {
        $user = $this->getUser($userId);
        if (!$user) return false;
        
        try {
            $stmt = $this->db->prepare("SELECT COUNT(*) as downloads_today FROM downloads WHERE user_id = ? AND DATE(download_date) = CURDATE()");
            $stmt->execute([$userId]);
            $todayDownloads = $stmt->fetch(PDO::FETCH_ASSOC)['downloads_today'];
            
            return [
                'total_downloads' => $user['total_downloads'],
                'downloads_today' => $todayDownloads,
                'remaining_today' => MAX_DOWNLOADS_PER_DAY - $todayDownloads,
                'join_date' => $user['join_date'],
                'is_banned' => $user['is_banned']
            ];
        } catch (PDOException $e) {
            return false;
        }
    }
    
    // Admin panel functions
    private function getAdminStats() {
        try {
            $stats = [];
            
            // Total users
            $stmt = $this->db->query("SELECT COUNT(*) as total FROM users");
            $stats['total_users'] = $stmt->fetch(PDO::FETCH_ASSOC)['total'];
            
            // Active users today
            $stmt = $this->db->query("SELECT COUNT(*) as active FROM users WHERE DATE(last_activity) = CURDATE()");
            $stats['active_today'] = $stmt->fetch(PDO::FETCH_ASSOC)['active'];
            
            // Total downloads
            $stmt = $this->db->query("SELECT COUNT(*) as total FROM downloads");
            $stats['total_downloads'] = $stmt->fetch(PDO::FETCH_ASSOC)['total'];
            
            // Downloads today
            $stmt = $this->db->query("SELECT COUNT(*) as today FROM downloads WHERE DATE(download_date) = CURDATE()");
            $stats['downloads_today'] = $stmt->fetch(PDO::FETCH_ASSOC)['today'];
            
            return $stats;
        } catch (PDOException $e) {
            return false;
        }
    }
    
    // Main keyboard for users
    private function getMainKeyboard() {
        return [
            'keyboard' => [
                [['text' => '📊 آمار من'], ['text' => '❓ راهنما']],
                [['text' => '📞 پشتیبانی'], ['text' => '🎯 درباره ربات']]
            ],
            'resize_keyboard' => true,
            'one_time_keyboard' => false
        ];
    }
    
    // Admin keyboard
    private function getAdminKeyboard() {
        return [
            'keyboard' => [
                [['text' => '📊 آمار کلی'], ['text' => '👥 مدیریت کاربران']],
                [['text' => '📈 گزارش دانلودها'], ['text' => '⚙️ تنظیمات']],
                [['text' => '📢 ارسال پیام همگانی'], ['text' => '🔙 بازگشت']]
            ],
            'resize_keyboard' => true,
            'one_time_keyboard' => false
        ];
    }
    
    // Process incoming message
    public function processMessage($update) {
        if (!isset($update['message'])) return;
        
        $message = $update['message'];
        $chatId = $message['chat']['id'];
        $userId = $message['from']['id'];
        $text = $message['text'] ?? '';
        $username = $message['from']['username'] ?? '';
        $firstName = $message['from']['first_name'] ?? '';
        $lastName = $message['from']['last_name'] ?? '';
        
        // Add/update user in database
        $this->addUser($userId, $username, $firstName, $lastName);
        
        // Handle commands and messages
        switch (true) {
            case $text === '/start':
                $this->handleStart($chatId, $firstName);
                break;
                
            case $text === '/panel' && $userId == $this->adminId:
                $this->handleAdminPanel($chatId);
                break;
                
            case $text === '📊 آمار من':
                $this->handleUserStats($chatId, $userId);
                break;
                
            case $text === '❓ راهنما':
                $this->handleHelp($chatId);
                break;
                
            case $text === '📞 پشتیبانی':
                $this->handleSupport($chatId);
                break;
                
            case $text === '🎯 درباره ربات':
                $this->handleAbout($chatId);
                break;
                
            case $text === '📊 آمار کلی' && $userId == $this->adminId:
                $this->handleAdminStats($chatId);
                break;
                
            case $text === '👥 مدیریت کاربران' && $userId == $this->adminId:
                $this->handleUserManagement($chatId);
                break;
                
            case $text === '🔙 بازگشت':
                $this->handleStart($chatId, $firstName);
                break;
                
            case strpos($text, 'instagram.com') !== false:
                $this->handleInstagramDownload($chatId, $userId, $text);
                break;
                
            default:
                $this->handleInvalidInput($chatId);
                break;
        }
    }
    
    private function handleStart($chatId, $firstName) {
        $welcomeText = "🎉 سلام $firstName! به ربات دانلود اینستاگرام خوش اومدی!\n\n";
        $welcomeText .= "🎬 برای دانلود ویدیو، لینک پست اینستاگرام رو برام بفرست\n";
        $welcomeText .= "📱 من همه نوع پست‌های اینستاگرام رو دانلود می‌کنم\n\n";
        $welcomeText .= "💡 روزانه " . MAX_DOWNLOADS_PER_DAY . " بار می‌تونی دانلود کنی\n";
        $welcomeText .= "⚡ دانلود سریع و با کیفیت بالا\n\n";
        $welcomeText .= "🔸 از منوی زیر استفاده کن:";
        
        $this->sendMessage($chatId, $welcomeText, $this->getMainKeyboard());
    }
    
    private function handleAdminPanel($chatId) {
        $stats = $this->getAdminStats();
        
        $adminText = "🔧 <b>پنل مدیریت ربات</b>\n\n";
        $adminText .= "👥 تعداد کل کاربران: <code>" . $stats['total_users'] . "</code>\n";
        $adminText .= "🟢 کاربران فعال امروز: <code>" . $stats['active_today'] . "</code>\n";
        $adminText .= "📥 کل دانلودها: <code>" . $stats['total_downloads'] . "</code>\n";
        $adminText .= "📅 دانلودهای امروز: <code>" . $stats['downloads_today'] . "</code>\n\n";
        $adminText .= "از منوی زیر برای مدیریت استفاده کنید:";
        
        $this->sendMessage($chatId, $adminText, $this->getAdminKeyboard());
    }
    
    private function handleUserStats($chatId, $userId) {
        $stats = $this->getUserStats($userId);
        
        if (!$stats) {
            $this->sendMessage($chatId, "❌ خطا در دریافت آمار");
            return;
        }
        
        $statsText = "📊 <b>آمار شما</b>\n\n";
        $statsText .= "📈 کل دانلودها: <code>" . $stats['total_downloads'] . "</code>\n";
        $statsText .= "📅 دانلودهای امروز: <code>" . $stats['downloads_today'] . "</code>\n";
        $statsText .= "⏳ باقیمانده امروز: <code>" . $stats['remaining_today'] . "</code>\n";
        $statsText .= "📅 تاریخ عضویت: <code>" . date('Y-m-d', strtotime($stats['join_date'])) . "</code>\n\n";
        
        if ($stats['is_banned']) {
            $statsText .= "🚫 <b>حساب شما مسدود شده است</b>";
        } else {
            $statsText .= "✅ وضعیت حساب: فعال";
        }
        
        $this->sendMessage($chatId, $statsText);
    }
    
    private function handleHelp($chatId) {
        $helpText = "❓ <b>راهنمای استفاده</b>\n\n";
        $helpText .= "🔸 لینک پست اینستاگرام رو کپی کنید\n";
        $helpText .= "🔸 لینک رو برای ربات بفرستید\n";
        $helpText .= "🔸 منتظر بمونید تا ربات فایل رو برای شما بفرسته\n\n";
        $helpText .= "📝 <b>نکات مهم:</b>\n";
        $helpText .= "• پست باید عمومی باشه\n";
        $helpText .= "• روزانه حداکثر " . MAX_DOWNLOADS_PER_DAY . " بار می‌تونید دانلود کنید\n";
        $helpText .= "• حداکثر حجم فایل " . (MAX_FILE_SIZE / 1024 / 1024) . " مگابایت\n";
        $helpText .= "• هم ویدیو و هم عکس پشتیبانی می‌شه\n\n";
        $helpText .= "💡 مثال لینک معتبر:\n";
        $helpText .= "<code>https://www.instagram.com/p/ABC123/</code>";
        
        $this->sendMessage($chatId, $helpText);
    }
    
    private function handleSupport($chatId) {
        $supportText = "📞 <b>پشتیبانی</b>\n\n";
        $supportText .= "🆔 آیدی پشتیبانی: @your_support_username\n";
        $supportText .= "📧 ایمیل: support@yourbot.com\n\n";
        $supportText .= "⏰ پاسخگویی: ۹ صبح تا ۱۲ شب\n";
        $supportText .= "🔸 در صورت بروز مشکل، لطفاً با ما تماس بگیرید";
        
        $this->sendMessage($chatId, $supportText);
    }
    
    private function handleAbout($chatId) {
        $aboutText = "🎯 <b>درباره ربات</b>\n\n";
        $aboutText .= "🤖 نام: " . BOT_NAME . "\n";
        $aboutText .= "📱 نسخه: 1.0\n";
        $aboutText .= "👨‍💻 سازنده: Your Name\n\n";
        $aboutText .= "✨ امکانات:\n";
        $aboutText .= "• دانلود ویدیو و عکس از اینستاگرام\n";
        $aboutText .= "• پنل کاربری پیشرفته\n";
        $aboutText .= "• آمار دانلود\n";
        $aboutText .= "• پشتیبانی از انواع فرمت\n";
        $aboutText .= "• سرعت بالا و کیفیت عالی\n\n";
        $aboutText .= "💝 با تشکر از استفاده شما";
        
        $this->sendMessage($chatId, $aboutText);
    }
    
    private function handleAdminStats($chatId) {
        $stats = $this->getAdminStats();
        
        $statsText = "📊 <b>آمار کلی سیستم</b>\n\n";
        $statsText .= "👥 کل کاربران: <code>" . $stats['total_users'] . "</code>\n";
        $statsText .= "🟢 فعال امروز: <code>" . $stats['active_today'] . "</code>\n";
        $statsText .= "📊 میانگین فعالیت: <code>" . round(($stats['active_today'] / max($stats['total_users'], 1)) * 100, 2) . "%</code>\n\n";
        $statsText .= "📥 کل دانلودها: <code>" . $stats['total_downloads'] . "</code>\n";
        $statsText .= "📅 دانلود امروز: <code>" . $stats['downloads_today'] . "</code>\n";
        $statsText .= "📊 میانگین دانلود: <code>" . round($stats['total_downloads'] / max($stats['total_users'], 1), 2) . "</code> فایل در هر کاربر\n\n";
        
        // Memory usage
        $statsText .= "💾 استفاده از حافظه: <code>" . round(memory_get_usage() / 1024 / 1024, 2) . " MB</code>\n";
        $statsText .= "⏰ زمان سرور: <code>" . date('Y-m-d H:i:s') . "</code>";
        
        $this->sendMessage($chatId, $statsText);
    }
    
    private function handleUserManagement($chatId) {
        try {
            $stmt = $this->db->query("SELECT id, username, first_name, total_downloads, is_banned, last_activity FROM users ORDER BY total_downloads DESC LIMIT 10");
            $users = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            $text = "👥 <b>10 کاربر برتر</b>\n\n";
            
            foreach ($users as $index => $user) {
                $status = $user['is_banned'] ? '🚫' : '✅';
                $username = $user['username'] ? '@' . $user['username'] : 'بدون نام کاربری';
                $lastActivity = date('Y-m-d', strtotime($user['last_activity']));
                
                $text .= ($index + 1) . ". $status " . ($user['first_name'] ?? 'ناشناس') . "\n";
                $text .= "   📱 $username\n";
                $text .= "   📊 " . $user['total_downloads'] . " دانلود\n";
                $text .= "   🕐 $lastActivity\n\n";
            }
            
            $this->sendMessage($chatId, $text);
        } catch (PDOException $e) {
            $this->sendMessage($chatId, "❌ خطا در دریافت اطلاعات کاربران");
        }
    }
    
    private function handleInstagramDownload($chatId, $userId, $url) {
        // Check if user can download
        if (!$this->canUserDownload($userId)) {
            $user = $this->getUser($userId);
            if ($user['is_banned']) {
                $this->sendMessage($chatId, "🚫 حساب شما مسدود شده است");
                return;
            }
            
            $this->sendMessage($chatId, "⚠️ شما به حد مجاز دانلود روزانه رسیده‌اید\n\nحد مجاز: " . MAX_DOWNLOADS_PER_DAY . " دانلود در روز");
            return;
        }
        
        $this->sendMessage($chatId, "⏳ در حال پردازش... لطفا صبر کنید");
        
        // Extract video URL
        $videoUrl = $this->getInstagramVideoUrl($url);
        
        if (!$videoUrl) {
            $this->sendMessage($chatId, "❌ خطا در دانلود!\n\n🔸 لینک نامعتبر است\n🔸 پست خصوصی است\n🔸 پست حذف شده است\n\nلطفا لینک دیگری امتحان کنید");
            return;
        }
        
        // Try to send video
        $result = $this->sendVideo($chatId, $videoUrl, "✅ دانلود موفق!\n\n📱 @" . BOT_NAME);
        
        if ($result && $result['ok']) {
            // Update user statistics
            $this->incrementDownloads($userId);
            $this->addDownloadRecord($userId, $url, 'video', 0);
            
            $this->sendMessage($chatId, "🎉 فایل با موفقیت ارسال شد!\n\n📊 برای مشاهده آمار از منو استفاده کنید");
        } else {
            // Try as document if video failed
            $docResult = $this->sendDocument($chatId, $videoUrl, "✅ دانلود موفق!");
            
            if ($docResult && $docResult['ok']) {
                $this->incrementDownloads($userId);
                $this->addDownloadRecord($userId, $url, 'document', 0);
                $this->sendMessage($chatId, "🎉 فایل به عنوان سند ارسال شد!");
            } else {
                $this->sendMessage($chatId, "❌ خطا در ارسال فایل!\n\nممکن است فایل خیلی بزرگ باشد");
            }
        }
    }
    
    private function handleInvalidInput($chatId) {
        $this->sendMessage($chatId, "❓ متوجه نشدم!\n\n🔸 لینک اینستاگرام بفرستید\n🔸 یا از منوی زیر استفاده کنید", $this->getMainKeyboard());
    }
}

// Handle webhook
$input = file_get_contents('php://input');
$update = json_decode($input, true);

if ($update) {
    $bot = new TelegramBot();
    $bot->processMessage($update);
}
?>