<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
require_once 'config.php';

// Logger function
function writeLog($message) {
    $log = date('Y-m-d H:i:s') . " - " . $message . "\n";
    file_put_contents('bot_log.txt', $log, FILE_APPEND | LOCK_EX);
}

class TelegramBot {
    private $botToken;
    private $adminId;
    private $db;
    
    public function __construct() {
        $this->botToken = BOT_TOKEN;
        $this->adminId = ADMIN_ID;
        $this->db = $this->initializeDatabase();
        writeLog("Bot initialized successfully");
    }
    
    private function initializeDatabase() {
        try {
            $pdo = new PDO("mysql:host=".DB_HOST.";dbname=".DB_NAME.";charset=utf8mb4", DB_USER, DB_PASS);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
            
            // Reset daily downloads at midnight
            $pdo->exec("UPDATE users SET downloads_today = 0 WHERE DATE(last_activity) < CURDATE()");
            
            writeLog("Database connected successfully");
            return $pdo;
        } catch(PDOException $e) {
            writeLog("Database connection failed: " . $e->getMessage());
            return false;
        }
    }
    
    // Send message to Telegram with better error handling
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
        
        $result = $this->makeRequest($url, $data);
        if (!$result || !$result['ok']) {
            writeLog("Failed to send message to $chatId: " . json_encode($result));
        }
        return $result;
    }
    
    // Send video with proper error handling
    private function sendVideo($chatId, $videoUrl, $caption = '') {
        $url = "https://api.telegram.org/bot" . $this->botToken . "/sendVideo";
        $data = [
            'chat_id' => $chatId,
            'video' => $videoUrl,
            'caption' => $caption,
            'parse_mode' => 'HTML',
            'supports_streaming' => true
        ];
        
        return $this->makeRequest($url, $data);
    }
    
    // Send document with proper error handling
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
    
    // Send photo
    private function sendPhoto($chatId, $photoUrl, $caption = '') {
        $url = "https://api.telegram.org/bot" . $this->botToken . "/sendPhoto";
        $data = [
            'chat_id' => $chatId,
            'photo' => $photoUrl,
            'caption' => $caption,
            'parse_mode' => 'HTML'
        ];
        
        return $this->makeRequest($url, $data);
    }
    
    // Enhanced HTTP request function
    private function makeRequest($url, $data) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_TIMEOUT, 60);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 30);
        
        $result = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode !== 200) {
            writeLog("HTTP request failed with code: $httpCode");
            return false;
        }
        
        return json_decode($result, true);
    }
    
    // Enhanced Instagram downloader with multiple methods
    private function downloadInstagramMedia($url) {
        writeLog("Attempting to download: $url");
        
        // Clean and validate URL
        $url = trim($url);
        if (!preg_match('/instagram\.com\/(?:p|reel|tv)\/([A-Za-z0-9_-]+)/', $url, $matches)) {
            writeLog("Invalid Instagram URL: $url");
            return false;
        }
        
        $shortcode = $matches[1];
        writeLog("Extracted shortcode: $shortcode");
        
        // Method 1: Try Instagram API endpoint
        $result = $this->tryInstagramAPI($url, $shortcode);
        if ($result) {
            writeLog("Successfully downloaded via Instagram API");
            return $result;
        }
        
        // Method 2: Try alternative scraping
        $result = $this->tryInstagramScraping($url);
        if ($result) {
            writeLog("Successfully downloaded via scraping");
            return $result;
        }
        
        // Method 3: Try rapid API (third-party)
        $result = $this->tryRapidAPI($shortcode);
        if ($result) {
            writeLog("Successfully downloaded via Rapid API");
            return $result;
        }
        
        writeLog("All download methods failed for: $url");
        return false;
    }
    
    private function tryInstagramAPI($url, $shortcode) {
        try {
            // Try with ?__a=1&__d=dis
            $apiUrl = "https://www.instagram.com/p/$shortcode/?__a=1&__d=dis";
            
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $apiUrl);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36');
            curl_setopt($ch, CURLOPT_TIMEOUT, 30);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language: en-US,en;q=0.5',
                'Accept-Encoding: gzip, deflate',
                'Connection: keep-alive',
                'Upgrade-Insecure-Requests: 1',
                'X-Requested-With: XMLHttpRequest'
            ]);
            
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            if ($httpCode === 200 && $response) {
                $data = json_decode($response, true);
                
                if (isset($data['items'][0])) {
                    $item = $data['items'][0];
                    
                    // Check for video
                    if (isset($item['video_versions']) && !empty($item['video_versions'])) {
                        return [
                            'type' => 'video',
                            'url' => $item['video_versions'][0]['url'],
                            'thumbnail' => $item['image_versions2']['candidates'][0]['url'] ?? null
                        ];
                    }
                    
                    // Check for photo
                    if (isset($item['image_versions2']['candidates'])) {
                        return [
                            'type' => 'photo',
                            'url' => $item['image_versions2']['candidates'][0]['url']
                        ];
                    }
                }
                
                // Try graphql structure
                if (isset($data['graphql']['shortcode_media'])) {
                    $media = $data['graphql']['shortcode_media'];
                    
                    if ($media['is_video'] && isset($media['video_url'])) {
                        return [
                            'type' => 'video',
                            'url' => $media['video_url'],
                            'thumbnail' => $media['display_url'] ?? null
                        ];
                    } else {
                        return [
                            'type' => 'photo',
                            'url' => $media['display_url']
                        ];
                    }
                }
            }
            
            return false;
        } catch (Exception $e) {
            writeLog("Instagram API method failed: " . $e->getMessage());
            return false;
        }
    }
    
    private function tryInstagramScraping($url) {
        try {
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $url);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1');
            curl_setopt($ch, CURLOPT_TIMEOUT, 30);
            
            $html = curl_exec($ch);
            curl_close($ch);
            
            if (!$html) return false;
            
            // Try to extract video URL from HTML
            if (preg_match('/"video_url":"([^"]+)"/', $html, $matches)) {
                $videoUrl = str_replace('\u0026', '&', $matches[1]);
                return [
                    'type' => 'video',
                    'url' => $videoUrl
                ];
            }
            
            // Try to extract photo URL
            if (preg_match('/"display_url":"([^"]+)"/', $html, $matches)) {
                $photoUrl = str_replace('\u0026', '&', $matches[1]);
                return [
                    'type' => 'photo',
                    'url' => $photoUrl
                ];
            }
            
            // Alternative pattern for photos
            if (preg_match('/property="og:image" content="([^"]+)"/', $html, $matches)) {
                return [
                    'type' => 'photo',
                    'url' => $matches[1]
                ];
            }
            
            return false;
        } catch (Exception $e) {
            writeLog("Instagram scraping failed: " . $e->getMessage());
            return false;
        }
    }
    
    private function tryRapidAPI($shortcode) {
        // This is a placeholder for RapidAPI integration
        // You can integrate with services like Instagram-scraper-2022 from RapidAPI
        return false;
    }
    
    // User management functions with better error handling
    private function addUser($userId, $username, $firstName, $lastName) {
        if (!$this->db) return false;
        
        try {
            $stmt = $this->db->prepare("INSERT INTO users (id, username, first_name, last_name, join_date, last_activity) 
                                       VALUES (?, ?, ?, ?, NOW(), NOW()) 
                                       ON DUPLICATE KEY UPDATE 
                                       username=VALUES(username), 
                                       first_name=VALUES(first_name), 
                                       last_name=VALUES(last_name), 
                                       last_activity=NOW()");
            $result = $stmt->execute([$userId, $username, $firstName, $lastName]);
            writeLog("User added/updated: $userId");
            return $result;
        } catch (PDOException $e) {
            writeLog("Failed to add user: " . $e->getMessage());
            return false;
        }
    }
    
    private function getUser($userId) {
        if (!$this->db) return false;
        
        try {
            $stmt = $this->db->prepare("SELECT * FROM users WHERE id = ?");
            $stmt->execute([$userId]);
            return $stmt->fetch();
        } catch (PDOException $e) {
            writeLog("Failed to get user: " . $e->getMessage());
            return false;
        }
    }
    
    private function incrementDownloads($userId) {
        if (!$this->db) return false;
        
        try {
            $stmt = $this->db->prepare("UPDATE users SET 
                                       downloads_today = downloads_today + 1, 
                                       total_downloads = total_downloads + 1,
                                       last_activity = NOW()
                                       WHERE id = ?");
            return $stmt->execute([$userId]);
        } catch (PDOException $e) {
            writeLog("Failed to increment downloads: " . $e->getMessage());
            return false;
        }
    }
    
    private function addDownloadRecord($userId, $url, $fileType, $fileSize = 0) {
        if (!$this->db) return false;
        
        try {
            $stmt = $this->db->prepare("INSERT INTO downloads (user_id, url, file_type, file_size, download_date) 
                                       VALUES (?, ?, ?, ?, NOW())");
            return $stmt->execute([$userId, $url, $fileType, $fileSize]);
        } catch (PDOException $e) {
            writeLog("Failed to add download record: " . $e->getMessage());
            return false;
        }
    }
    
    // Check if user can download with proper validation
    private function canUserDownload($userId) {
        $user = $this->getUser($userId);
        if (!$user) return false;
        
        // Reset daily count if it's a new day
        if (date('Y-m-d', strtotime($user['last_activity'])) < date('Y-m-d')) {
            try {
                $stmt = $this->db->prepare("UPDATE users SET downloads_today = 0 WHERE id = ?");
                $stmt->execute([$userId]);
                $user['downloads_today'] = 0;
            } catch (PDOException $e) {
                writeLog("Failed to reset daily downloads: " . $e->getMessage());
            }
        }
        
        return $user['downloads_today'] < MAX_DOWNLOADS_PER_DAY && !$user['is_banned'];
    }
    
    // Get accurate user statistics
    private function getUserStats($userId) {
        $user = $this->getUser($userId);
        if (!$user) return false;
        
        try {
            // Get today's downloads from downloads table
            $stmt = $this->db->prepare("SELECT COUNT(*) as downloads_today 
                                       FROM downloads 
                                       WHERE user_id = ? AND DATE(download_date) = CURDATE()");
            $stmt->execute([$userId]);
            $todayDownloads = $stmt->fetch()['downloads_today'];
            
            // Get total downloads
            $stmt = $this->db->prepare("SELECT COUNT(*) as total_downloads 
                                       FROM downloads 
                                       WHERE user_id = ?");
            $stmt->execute([$userId]);
            $totalDownloads = $stmt->fetch()['total_downloads'];
            
            return [
                'total_downloads' => $totalDownloads,
                'downloads_today' => $todayDownloads,
                'remaining_today' => max(0, MAX_DOWNLOADS_PER_DAY - $todayDownloads),
                'join_date' => $user['join_date'],
                'last_activity' => $user['last_activity'],
                'is_banned' => $user['is_banned'],
                'username' => $user['username'],
                'first_name' => $user['first_name']
            ];
        } catch (PDOException $e) {
            writeLog("Failed to get user stats: " . $e->getMessage());
            return false;
        }
    }
    
    // Enhanced admin statistics
    private function getAdminStats() {
        if (!$this->db) return false;
        
        try {
            $stats = [];
            
            // Total users
            $stmt = $this->db->query("SELECT COUNT(*) as total FROM users");
            $stats['total_users'] = $stmt->fetch()['total'];
            
            // Active users today
            $stmt = $this->db->query("SELECT COUNT(*) as active 
                                     FROM users 
                                     WHERE DATE(last_activity) = CURDATE()");
            $stats['active_today'] = $stmt->fetch()['active'];
            
            // Active users this week
            $stmt = $this->db->query("SELECT COUNT(*) as active 
                                     FROM users 
                                     WHERE last_activity >= DATE_SUB(NOW(), INTERVAL 7 DAY)");
            $stats['active_week'] = $stmt->fetch()['active'];
            
            // Total downloads
            $stmt = $this->db->query("SELECT COUNT(*) as total FROM downloads");
            $stats['total_downloads'] = $stmt->fetch()['total'];
            
            // Downloads today
            $stmt = $this->db->query("SELECT COUNT(*) as today 
                                     FROM downloads 
                                     WHERE DATE(download_date) = CURDATE()");
            $stats['downloads_today'] = $stmt->fetch()['today'];
            
            // Downloads this week
            $stmt = $this->db->query("SELECT COUNT(*) as week 
                                     FROM downloads 
                                     WHERE download_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)");
            $stats['downloads_week'] = $stmt->fetch()['week'];
            
            // New users today
            $stmt = $this->db->query("SELECT COUNT(*) as new_today 
                                     FROM users 
                                     WHERE DATE(join_date) = CURDATE()");
            $stats['new_users_today'] = $stmt->fetch()['new_today'];
            
            return $stats;
        } catch (PDOException $e) {
            writeLog("Failed to get admin stats: " . $e->getMessage());
            return false;
        }
    }
    
    // Enhanced keyboards
    private function getMainKeyboard() {
        return [
            'keyboard' => [
                [['text' => '📊 آمار من'], ['text' => '❓ راهنما']],
                [['text' => '📞 پشتیبانی'], ['text' => '🎯 درباره ربات']],
                [['text' => '🔄 آخرین دانلودها']]
            ],
            'resize_keyboard' => true,
            'one_time_keyboard' => false
        ];
    }
    
    private function getAdminKeyboard() {
        return [
            'keyboard' => [
                [['text' => '📊 آمار کلی'], ['text' => '👥 مدیریت کاربران']],
                [['text' => '📈 گزارش دانلودها'], ['text' => '⚙️ تنظیمات']],
                [['text' => '📢 ارسال پیام همگانی'], ['text' => '🗑️ پاک کردن لاگ']],
                [['text' => '🔙 بازگشت']]
            ],
            'resize_keyboard' => true,
            'one_time_keyboard' => false
        ];
    }
    
    // Enhanced message processing
    public function processMessage($update) {
        if (!isset($update['message'])) {
            writeLog("No message in update: " . json_encode($update));
            return;
        }
        
        $message = $update['message'];
        $chatId = $message['chat']['id'];
        $userId = $message['from']['id'];
        $text = $message['text'] ?? '';
        $username = $message['from']['username'] ?? '';
        $firstName = $message['from']['first_name'] ?? '';
        $lastName = $message['from']['last_name'] ?? '';
        
        writeLog("Processing message from user $userId: $text");
        
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
                
            case $text === '🔄 آخرین دانلودها':
                $this->handleRecentDownloads($chatId, $userId);
                break;
                
            case $text === '📊 آمار کلی' && $userId == $this->adminId:
                $this->handleAdminStats($chatId);
                break;
                
            case $text === '👥 مدیریت کاربران' && $userId == $this->adminId:
                $this->handleUserManagement($chatId);
                break;
                
            case $text === '📈 گزارش دانلودها' && $userId == $this->adminId:
                $this->handleDownloadReports($chatId);
                break;
                
            case $text === '🗑️ پاک کردن لاگ' && $userId == $this->adminId:
                $this->handleClearLog($chatId);
                break;
                
            case $text === '🔙 بازگشت':
                $this->handleStart($chatId, $firstName);
                break;
                
            case preg_match('/instagram\.com\/(?:p|reel|tv)\//', $text):
                $this->handleInstagramDownload($chatId, $userId, $text);
                break;
                
            default:
                $this->handleInvalidInput($chatId);
                break;
        }
    }
    
    private function handleStart($chatId, $firstName) {
        $welcomeText = "🎉 سلام <b>$firstName</b>! به ربات دانلود اینستاگرام خوش اومدی!\n\n";
        $welcomeText .= "🎬 برای دانلود ویدیو یا عکس، لینک پست اینستاگرام رو برام بفرست\n";
        $welcomeText .= "📱 من همه نوع پست‌های اینستاگرام رو دانلود می‌کنم\n\n";
        $welcomeText .= "💡 روزانه " . MAX_DOWNLOADS_PER_DAY . " بار می‌تونی دانلود کنی\n";
        $welcomeText .= "⚡ دانلود سریع و با کیفیت بالا\n\n";
        $welcomeText .= "🔸 از منوی زیر استفاده کن:";
        
        $this->sendMessage($chatId, $welcomeText, $this->getMainKeyboard());
    }
    
    private function handleAdminPanel($chatId) {
        $stats = $this->getAdminStats();
        if (!$stats) {
            $this->sendMessage($chatId, "❌ خطا در دریافت آمار");
            return;
        }
        
        $adminText = "🔧 <b>پنل مدیریت ربات</b>\n\n";
        $adminText .= "👥 کل کاربران: <code>" . number_format($stats['total_users']) . "</code>\n";
        $adminText .= "🟢 فعال امروز: <code>" . number_format($stats['active_today']) . "</code>\n";
        $adminText .= "📊 فعال این هفته: <code>" . number_format($stats['active_week']) . "</code>\n";
        $adminText .= "🆕 عضو جدید امروز: <code>" . number_format($stats['new_users_today']) . "</code>\n\n";
        $adminText .= "📥 کل دانلودها: <code>" . number_format($stats['total_downloads']) . "</code>\n";
        $adminText .= "📅 دانلود امروز: <code>" . number_format($stats['downloads_today']) . "</code>\n";
        $adminText .= "📈 دانلود این هفته: <code>" . number_format($stats['downloads_week']) . "</code>\n\n";
        $adminText .= "💾 حافظه: <code>" . round(memory_get_usage() / 1024 / 1024, 2) . " MB</code>\n";
        $adminText .= "⏰ زمان سرور: <code>" . date('Y-m-d H:i:s') . "</code>\n\n";
        $adminText .= "از منوی زیر برای مدیریت استفاده کنید:";
        
        $this->sendMessage($chatId, $adminText, $this->getAdminKeyboard());
    }
    
    private function handleUserStats($chatId, $userId) {
        $stats = $this->getUserStats($userId);
        
        if (!$stats) {
            $this->sendMessage($chatId, "❌ خطا در دریافت آمار شما");
            return;
        }
        
        $statsText = "📊 <b>آمار شما</b>\n\n";
        $statsText .= "👤 نام: <b>" . ($stats['first_name'] ?? 'نامشخص') . "</b>\n";
        if ($stats['username']) {
            $statsText .= "🆔 نام کاربری: @" . $stats['username'] . "\n";
        }
        $statsText .= "\n📈 <b>آمار دانلود:</b>\n";
        $statsText .= "📊 کل دانلودها: <code>" . number_format($stats['total_downloads']) . "</code>\n";
        $statsText .= "📅 دانلود امروز: <code>" . number_format($stats['downloads_today']) . "</code>\n";
        $statsText .= "⏳ باقیمانده امروز: <code>" . number_format($stats['remaining_today']) . "</code>\n\n";
        $statsText .= "📅 تاریخ عضویت: <code>" . date('Y-m-d H:i', strtotime($stats['join_date'])) . "</code>\n";
        $statsText .= "🕐 آخرین فعالیت: <code>" . date('Y-m-d H:i', strtotime($stats['last_activity'])) . "</code>\n\n";
        
        if ($stats['is_banned']) {
            $statsText .= "🚫 <b>حساب شما مسدود شده است</b>\n";
            $statsText .= "برای رفع مسدودیت با پشتیبانی تماس بگیرید";
        } else {
            $statsText .= "✅ وضعیت حساب: <b>فعال</b>";
        }
        
        $this->sendMessage($chatId, $statsText);
    }
    
    private function handleHelp($chatId) {
        $helpText = "❓ <b>راهنمای استفاده از ربات</b>\n\n";
        $helpText .= "🔸 لینک پست اینستاگرام رو کپی کنید\n";
        $helpText .= "🔸 لینک رو برای ربات بفرستید\n";
        $helpText .= "🔸 منتظر بمونید تا ربات فایل رو برای شما بفرسته\n\n";
        $helpText .= "📝 <b>نکات مهم:</b>\n";
        $helpText .= "• پست باید عمومی باشه (خصوصی نباشه)\n";
        $helpText .= "• روزانه حداکثر " . MAX_DOWNLOADS_PER_DAY . " بار می‌تونید دانلود کنید\n";
        $helpText .= "• حداکثر حجم فایل " . (MAX_FILE_SIZE / 1024 / 1024) . " مگابایت\n";
        $helpText .= "• هم ویدیو و هم عکس پشتیبانی می‌شه\n";
        $helpText .= "• از ریل، IGTV و پست‌های عادی پشتیبانی می‌کنیم\n\n";
        $helpText .= "💡 <b>نمونه لینک‌های معتبر:</b>\n";
        $helpText .= "<code>https://www.instagram.com/p/ABC123/</code>\n";
        $helpText .= "<code>https://www.instagram.com/reel/XYZ789/</code>\n";
        $helpText .= "<code>https://www.instagram.com/tv/DEF456/</code>\n\n";
        $helpText .= "❓ سوال دارید؟ از دکمه پشتیبانی استفاده کنید";
        
        $this->sendMessage($chatId, $helpText);
    }
    
    private function handleSupport($chatId) {
        $supportText = "📞 <b>پشتیبانی و ارتباط</b>\n\n";
        $supportText .= "🆔 آیدی پشتیبانی: <code>در حال بروزرسانی</code>\n";
        $supportText .= "📧 ایمیل: <code>support@instagram-downloader.com</code>\n";
        $supportText .= "🌐 وبسایت: <code>در حال راه‌اندازی</code>\n\n";
        $supportText .= "⏰ <b>ساعات پاسخگویی:</b>\n";
        $supportText .= "🕘 شنبه تا پنج‌شنبه: ۹ صبح تا ۱۲ شب\n";
        $supportText .= "🕘 جمعه: ۱۴ تا ۲۲\n\n";
        $supportText .= "🔸 در صورت بروز مشکل فنی یا سوال، با ما تماس بگیرید\n";
        $supportText .= "🔸 پیشنهادات خود را با ما در میان بذارید\n";
        $supportText .= "🔸 برای گزارش باگ از این بخش استفاده کنید";
        
        $this->sendMessage($chatId, $supportText);
    }
    
    private function handleAbout($chatId) {
        $aboutText = "🎯 <b>درباره ربات دانلود اینستاگرام</b>\n\n";
        $aboutText .= "🤖 نام: " . BOT_NAME . "\n";
        $aboutText .= "📱 نسخه: 2.0 - پیشرفته\n";
        $aboutText .= "👨‍💻 سازنده: تیم توسعه\n";
        $aboutText .= "📅 تاریخ انتشار: " . date('Y-m-d') . "\n\n";
        $aboutText .= "✨ <b>امکانات:</b>\n";
        $aboutText .= "• دانلود ویدیو و عکس از اینستاگرام\n";
        $aboutText .= "• پشتیبانی از ریل، IGTV و پست‌های عادی\n";
        $aboutText .= "• پنل کاربری پیشرفته با آمار دقیق\n";
        $aboutText .= "• پنل مدیریت کامل\n";
        $aboutText .= "• سیستم محدودیت روزانه\n";
        $aboutText .= "• چندین روش دانلود برای اطمینان\n";
        $aboutText .= "• رابط کاربری فارسی\n";
        $aboutText .= "• سرعت بالا و کیفیت عالی\n";
        $aboutText .= "• سیستم لاگ پیشرفته\n\n";
        $aboutText .= "🔧 <b>ویژگی‌های فنی:</b>\n";
        $aboutText .= "• پشتیبانی از فرمت‌های مختلف\n";
        $aboutText .= "• بهینه‌سازی برای سرعت\n";
        $aboutText .= "• امنیت بالا\n";
        $aboutText .= "• پایگاه داده پیشرفته\n\n";
        $aboutText .= "💝 با تشکر از استفاده شما\n";
        $aboutText .= "🌟 ربات را به دوستان خود معرفی کنید";
        
        $this->sendMessage($chatId, $aboutText);
    }
    
    private function handleRecentDownloads($chatId, $userId) {
        if (!$this->db) {
            $this->sendMessage($chatId, "❌ خطا در اتصال به پایگاه داده");
            return;
        }
        
        try {
            $stmt = $this->db->prepare("SELECT url, file_type, download_date 
                                       FROM downloads 
                                       WHERE user_id = ? 
                                       ORDER BY download_date DESC 
                                       LIMIT 10");
            $stmt->execute([$userId]);
            $downloads = $stmt->fetchAll();
            
            if (empty($downloads)) {
                $this->sendMessage($chatId, "📭 شما هنوز هیچ فایلی دانلود نکرده‌اید\n\nلینک اینستاگرام بفرستید تا براتون دانلود کنم! 😊");
                return;
            }
            
            $text = "🔄 <b>آخرین دانلودهای شما</b>\n\n";
            
            foreach ($downloads as $index => $download) {
                $date = date('Y-m-d H:i', strtotime($download['download_date']));
                $shortUrl = substr($download['url'], 0, 40) . '...';
                $typeEmoji = $download['file_type'] === 'video' ? '🎬' : '📷';
                
                $text .= ($index + 1) . ". $typeEmoji " . $download['file_type'] . "\n";
                $text .= "   📅 $date\n";
                $text .= "   🔗 $shortUrl\n\n";
            }
            
            $text .= "💡 برای دانلود جدید، لینک جدید بفرستید";
            
            $this->sendMessage($chatId, $text);
        } catch (PDOException $e) {
            writeLog("Failed to get recent downloads: " . $e->getMessage());
            $this->sendMessage($chatId, "❌ خطا در دریافت اطلاعات دانلودها");
        }
    }
    
    private function handleAdminStats($chatId) {
        $stats = $this->getAdminStats();
        if (!$stats) {
            $this->sendMessage($chatId, "❌ خطا در دریافت آمار سیستم");
            return;
        }
        
        $statsText = "📊 <b>آمار تفصیلی سیستم</b>\n\n";
        
        // User statistics
        $statsText .= "👥 <b>آمار کاربران:</b>\n";
        $statsText .= "• کل کاربران: <code>" . number_format($stats['total_users']) . "</code>\n";
        $statsText .= "• فعال امروز: <code>" . number_format($stats['active_today']) . "</code>\n";
        $statsText .= "• فعال این هفته: <code>" . number_format($stats['active_week']) . "</code>\n";
        $statsText .= "• عضو جدید امروز: <code>" . number_format($stats['new_users_today']) . "</code>\n";
        
        if ($stats['total_users'] > 0) {
            $activePercent = round(($stats['active_today'] / $stats['total_users']) * 100, 2);
            $statsText .= "• درصد فعالیت: <code>$activePercent%</code>\n";
        }
        
        $statsText .= "\n📈 <b>آمار دانلودها:</b>\n";
        $statsText .= "• کل دانلودها: <code>" . number_format($stats['total_downloads']) . "</code>\n";
        $statsText .= "• دانلود امروز: <code>" . number_format($stats['downloads_today']) . "</code>\n";
        $statsText .= "• دانلود این هفته: <code>" . number_format($stats['downloads_week']) . "</code>\n";
        
        if ($stats['total_users'] > 0) {
            $avgDownloads = round($stats['total_downloads'] / $stats['total_users'], 2);
            $statsText .= "• میانگین دانلود: <code>$avgDownloads</code> فایل/کاربر\n";
        }
        
        // System info
        $statsText .= "\n🖥️ <b>اطلاعات سیستم:</b>\n";
        $statsText .= "• حافظه استفاده شده: <code>" . round(memory_get_usage() / 1024 / 1024, 2) . " MB</code>\n";
        $statsText .= "• حداکثر حافظه: <code>" . round(memory_get_peak_usage() / 1024 / 1024, 2) . " MB</code>\n";
        $statsText .= "• نسخه PHP: <code>" . PHP_VERSION . "</code>\n";
        $statsText .= "• زمان سرور: <code>" . date('Y-m-d H:i:s') . "</code>\n";
        $statsText .= "• زمان اجرا: <code>" . round(microtime(true) - $_SERVER["REQUEST_TIME_FLOAT"], 3) . " ثانیه</code>";
        
        $this->sendMessage($chatId, $statsText);
    }
    
    private function handleUserManagement($chatId) {
        if (!$this->db) {
            $this->sendMessage($chatId, "❌ خطا در اتصال به پایگاه داده");
            return;
        }
        
        try {
            // Get top users
            $stmt = $this->db->query("SELECT id, username, first_name, total_downloads, downloads_today, is_banned, 
                                     last_activity, join_date
                                     FROM users 
                                     ORDER BY total_downloads DESC 
                                     LIMIT 15");
            $users = $stmt->fetchAll();
            
            $text = "👥 <b>مدیریت کاربران (15 کاربر برتر)</b>\n\n";
            
            if (empty($users)) {
                $text .= "📭 هیچ کاربری یافت نشد";
            } else {
                foreach ($users as $index => $user) {
                    $status = $user['is_banned'] ? '🚫' : '✅';
                    $username = $user['username'] ? '@' . $user['username'] : 'بدون یوزرنیم';
                    $lastActivity = date('m-d H:i', strtotime($user['last_activity']));
                    $joinDate = date('Y-m-d', strtotime($user['join_date']));
                    
                    $text .= ($index + 1) . ". $status <b>" . ($user['first_name'] ?? 'نامشخص') . "</b>\n";
                    $text .= "   🆔 ID: <code>" . $user['id'] . "</code>\n";
                    $text .= "   📱 $username\n";
                    $text .= "   📊 کل: " . number_format($user['total_downloads']) . " | امروز: " . $user['downloads_today'] . "\n";
                    $text .= "   📅 عضویت: $joinDate\n";
                    $text .= "   🕐 آخرین: $lastActivity\n\n";
                }
                
                // Additional stats
                $stmt = $this->db->query("SELECT COUNT(*) as banned FROM users WHERE is_banned = 1");
                $bannedCount = $stmt->fetch()['banned'];
                
                $text .= "📊 <b>خلاصه:</b>\n";
                $text .= "🚫 کاربران مسدود: <code>" . number_format($bannedCount) . "</code>\n";
                $text .= "✅ کاربران فعال: <code>" . number_format(count($users) - $bannedCount) . "</code>";
            }
            
            $this->sendMessage($chatId, $text);
        } catch (PDOException $e) {
            writeLog("Failed to get user management data: " . $e->getMessage());
            $this->sendMessage($chatId, "❌ خطا در دریافت اطلاعات کاربران");
        }
    }
    
    private function handleDownloadReports($chatId) {
        if (!$this->db) {
            $this->sendMessage($chatId, "❌ خطا در اتصال به پایگاه داده");
            return;
        }
        
        try {
            $text = "📈 <b>گزارش تفصیلی دانلودها</b>\n\n";
            
            // Downloads by day (last 7 days)
            $stmt = $this->db->query("SELECT DATE(download_date) as date, COUNT(*) as count
                                     FROM downloads 
                                     WHERE download_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                                     GROUP BY DATE(download_date)
                                     ORDER BY date DESC");
            $dailyDownloads = $stmt->fetchAll();
            
            $text .= "📅 <b>دانلودهای 7 روز گذشته:</b>\n";
            if (empty($dailyDownloads)) {
                $text .= "📭 داده‌ای یافت نشد\n";
            } else {
                foreach ($dailyDownloads as $day) {
                    $date = date('Y-m-d', strtotime($day['date']));
                    $dayName = $this->getPersianDayName($day['date']);
                    $text .= "• $dayName ($date): <code>" . number_format($day['count']) . "</code> دانلود\n";
                }
            }
            
            // File type distribution
            $stmt = $this->db->query("SELECT file_type, COUNT(*) as count
                                     FROM downloads 
                                     GROUP BY file_type
                                     ORDER BY count DESC");
            $fileTypes = $stmt->fetchAll();
            
            $text .= "\n📁 <b>توزیع نوع فایل:</b>\n";
            foreach ($fileTypes as $type) {
                $emoji = $type['file_type'] === 'video' ? '🎬' : '📷';
                $text .= "• $emoji " . ucfirst($type['file_type']) . ": <code>" . number_format($type['count']) . "</code>\n";
            }
            
            // Peak hours
            $stmt = $this->db->query("SELECT HOUR(download_date) as hour, COUNT(*) as count
                                     FROM downloads 
                                     WHERE download_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                                     GROUP BY HOUR(download_date)
                                     ORDER BY count DESC
                                     LIMIT 5");
            $peakHours = $stmt->fetchAll();
            
            $text .= "\n🕐 <b>ساعات پرترافیک:</b>\n";
            foreach ($peakHours as $hour) {
                $hourFormatted = sprintf('%02d:00', $hour['hour']);
                $text .= "• $hourFormatted: <code>" . number_format($hour['count']) . "</code> دانلود\n";
            }
            
            $this->sendMessage($chatId, $text);
        } catch (PDOException $e) {
            writeLog("Failed to get download reports: " . $e->getMessage());
            $this->sendMessage($chatId, "❌ خطا در تولید گزارش دانلودها");
        }
    }
    
    private function getPersianDayName($date) {
        $dayOfWeek = date('w', strtotime($date));
        $persianDays = ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه'];
        return $persianDays[$dayOfWeek];
    }
    
    private function handleClearLog($chatId) {
        if (file_exists('bot_log.txt')) {
            $logSize = filesize('bot_log.txt');
            $logSizeMB = round($logSize / 1024 / 1024, 2);
            
            if (unlink('bot_log.txt')) {
                $this->sendMessage($chatId, "🗑️ <b>لاگ پاک شد</b>\n\nحجم پاک شده: <code>$logSizeMB MB</code>");
                writeLog("Log file cleared by admin");
            } else {
                $this->sendMessage($chatId, "❌ خطا در پاک کردن لاگ");
            }
        } else {
            $this->sendMessage($chatId, "📭 فایل لاگ وجود ندارد");
        }
    }
    
    private function handleInstagramDownload($chatId, $userId, $url) {
        // Check if user can download
        if (!$this->canUserDownload($userId)) {
            $user = $this->getUser($userId);
            if ($user && $user['is_banned']) {
                $this->sendMessage($chatId, "🚫 <b>حساب شما مسدود شده است</b>\n\nبرای رفع مسدودیت با پشتیبانی تماس بگیرید");
                return;
            }
            
            $this->sendMessage($chatId, "⚠️ <b>محدودیت دانلود روزانه</b>\n\nشما به حد مجاز دانلود روزانه رسیده‌اید\n\n📊 حد مجاز: " . MAX_DOWNLOADS_PER_DAY . " دانلود در روز\n🕐 ساعت ۰۰:۰۰ محدودیت ریست می‌شه");
            return;
        }
        
        // Send processing message
        $processingMsg = $this->sendMessage($chatId, "⏳ <b>در حال پردازش...</b>\n\n🔍 دریافت اطلاعات پست\n📥 آماده‌سازی دانلود\n\nلطفا صبر کنید...");
        
        // Download media
        $mediaData = $this->downloadInstagramMedia($url);
        
        if (!$mediaData) {
            $errorText = "❌ <b>خطا در دانلود!</b>\n\n";
            $errorText .= "🔸 لینک نامعتبر یا اشتباه است\n";
            $errorText .= "🔸 پست خصوصی است\n";
            $errorText .= "🔸 پست حذف شده است\n";
            $errorText .= "🔸 مشکل موقت در سرور اینستاگرام\n\n";
            $errorText .= "💡 لطفا:\n";
            $errorText .= "• لینک را دوباره چک کنید\n";
            $errorText .= "• مطمئن شوید پست عمومی است\n";
            $errorText .= "• چند دقیقه دیگر دوباره امتحان کنید";
            
            $this->sendMessage($chatId, $errorText);
            return;
        }
        
        $success = false;
        $fileType = $mediaData['type'];
        
        // Try to send based on media type
        if ($mediaData['type'] === 'video') {
            $result = $this->sendVideo($chatId, $mediaData['url'], "✅ <b>دانلود موفق!</b>\n\n🎬 ویدیو اینستاگرام\n📱 @InstagramDownloaderBot");
            if ($result && $result['ok']) {
                $success = true;
            } else {
                // Try as document if video failed
                $result = $this->sendDocument($chatId, $mediaData['url'], "✅ <b>دانلود موفق!</b>\n\n🎬 ویدیو اینستاگرام\n📱 @InstagramDownloaderBot");
                if ($result && $result['ok']) {
                    $success = true;
                    $fileType = 'document';
                }
            }
        } else {
            $result = $this->sendPhoto($chatId, $mediaData['url'], "✅ <b>دانلود موفق!</b>\n\n📷 عکس اینستاگرام\n📱 @InstagramDownloaderBot");
            if ($result && $result['ok']) {
                $success = true;
            } else {
                // Try as document if photo failed
                $result = $this->sendDocument($chatId, $mediaData['url'], "✅ <b>دانلود موفق!</b>\n\n📷 عکس اینستاگرام\n📱 @InstagramDownloaderBot");
                if ($result && $result['ok']) {
                    $success = true;
                    $fileType = 'document';
                }
            }
        }
        
        if ($success) {
            // Update user statistics
            $this->incrementDownloads($userId);
            $this->addDownloadRecord($userId, $url, $fileType, 0);
            
            $stats = $this->getUserStats($userId);
            $successText = "🎉 <b>فایل با موفقیت ارسال شد!</b>\n\n";
            $successText .= "📊 آمار شما:\n";
            $successText .= "• دانلود امروز: <code>" . $stats['downloads_today'] . "</code>\n";
            $successText .= "• باقیمانده: <code>" . $stats['remaining_today'] . "</code>\n";
            $successText .= "• کل دانلودها: <code>" . $stats['total_downloads'] . "</code>\n\n";
            $successText .= "💡 برای دانلود بیشتر، لینک جدید بفرستید!";
            
            $this->sendMessage($chatId, $successText);
            writeLog("Successful download for user $userId: $url");
        } else {
            $errorText = "❌ <b>خطا در ارسال فایل!</b>\n\n";
            $errorText .= "🔸 فایل خیلی بزرگ است (حداکثر " . (MAX_FILE_SIZE / 1024 / 1024) . " مگابایت)\n";
            $errorText .= "🔸 مشکل موقت در سرورهای تلگرام\n";
            $errorText .= "🔸 نوع فایل پشتیبانی نمی‌شود\n\n";
            $errorText .= "💡 لطفا چند دقیقه دیگر دوباره امتحان کنید";
            
            $this->sendMessage($chatId, $errorText);
            writeLog("Failed to send file for user $userId: $url");
        }
    }
    
    private function handleInvalidInput($chatId) {
        $this->sendMessage($chatId, "❓ <b>متوجه نشدم!</b>\n\n🔸 لینک اینستاگرام بفرستید\n🔸 یا از منوی زیر استفاده کنید\n\n💡 <b>مثال لینک صحیح:</b>\n<code>https://www.instagram.com/p/ABC123/</code>", $this->getMainKeyboard());
    }
}

// Main execution
try {
    $input = file_get_contents('php://input');
    writeLog("Received input: " . $input);
    
    $update = json_decode($input, true);
    
    if ($update && isset($update['message'])) {
        $bot = new TelegramBot();
        $bot->processMessage($update);
    } else {
        writeLog("Invalid update received: " . json_encode($update));
    }
} catch (Exception $e) {
    writeLog("Fatal error: " . $e->getMessage());
    error_log("Bot fatal error: " . $e->getMessage());
}
?>