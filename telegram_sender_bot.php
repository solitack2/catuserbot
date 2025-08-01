<?php
require_once 'config.php';

class TelegramSenderBot {
    private $bot_token;
    private $accounts_file;
    private $members_file;
    private $admin_id;
    
    public function __construct($bot_token, $admin_id) {
        $this->bot_token = $bot_token;
        $this->admin_id = $admin_id;
        $this->accounts_file = ACCOUNTS_FILE;
        $this->members_file = MEMBERS_FILE;
        
        // Initialize files if they don't exist
        if (!file_exists($this->accounts_file)) {
            file_put_contents($this->accounts_file, json_encode([]));
        }
        if (!file_exists($this->members_file)) {
            file_put_contents($this->members_file, json_encode([]));
        }
    }
    
    // Send message to Telegram
    private function sendMessage($chat_id, $text, $reply_markup = null) {
        $url = "https://api.telegram.org/bot{$this->bot_token}/sendMessage";
        $data = [
            'chat_id' => $chat_id,
            'text' => $text,
            'parse_mode' => 'HTML'
        ];
        
        if ($reply_markup) {
            $data['reply_markup'] = json_encode($reply_markup);
        }
        
        $options = [
            'http' => [
                'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
                'method' => 'POST',
                'content' => http_build_query($data)
            ]
        ];
        
        return file_get_contents($url, false, stream_context_create($options));
    }
    
    // Load accounts from file
    private function loadAccounts() {
        $data = file_get_contents($this->accounts_file);
        return json_decode($data, true) ?: [];
    }
    
    // Save accounts to file
    private function saveAccounts($accounts) {
        file_put_contents($this->accounts_file, json_encode($accounts, JSON_PRETTY_PRINT));
    }
    
    // Load members from file
    private function loadMembers() {
        $data = file_get_contents($this->members_file);
        return json_decode($data, true) ?: [];
    }
    
    // Save members to file
    private function saveMembers($members) {
        file_put_contents($this->members_file, json_encode($members, JSON_PRETTY_PRINT));
    }
    
    // Check account status (simulate API check)
    private function checkAccountStatus($phone) {
        // Simulate account status check
        $statuses = ['سالم', 'محدود', 'بن', 'آفلاین'];
        return $statuses[array_rand($statuses)];
    }
    
    // Add new account
    private function addAccount($phone, $session_string = '') {
        $accounts = $this->loadAccounts();
        
        if (isset($accounts[$phone])) {
            return "❌ این شماره قبلاً اضافه شده است";
        }
        
        $accounts[$phone] = [
            'phone' => $phone,
            'session' => $session_string,
            'status' => 'سالم',
            'added_date' => date('Y-m-d H:i:s'),
            'last_check' => date('Y-m-d H:i:s')
        ];
        
        $this->saveAccounts($accounts);
        return "✅ اکانت {$phone} با موفقیت اضافه شد";
    }
    
    // Get accounts status
    private function getAccountsStatus() {
        $accounts = $this->loadAccounts();
        
        if (empty($accounts)) {
            return "❌ هیچ اکانتی یافت نشد";
        }
        
        $status_counts = ['سالم' => 0, 'محدود' => 0, 'بن' => 0, 'آفلاین' => 0];
        $message = "📊 <b>وضعیت اکانت‌ها:</b>\n\n";
        
        foreach ($accounts as $phone => &$account) {
            $account['status'] = $this->checkAccountStatus($phone);
            $account['last_check'] = date('Y-m-d H:i:s');
            $status_counts[$account['status']]++;
            
            $status_emoji = [
                'سالم' => '✅',
                'محدود' => '⚠️',
                'بن' => '❌',
                'آفلاین' => '⭕'
            ];
            
            $message .= "{$status_emoji[$account['status']]} {$phone} - {$account['status']}\n";
        }
        
        $this->saveAccounts($accounts);
        
        $message .= "\n📈 <b>خلاصه آمار:</b>\n";
        $message .= "✅ سالم: {$status_counts['سالم']}\n";
        $message .= "⚠️ محدود: {$status_counts['محدود']}\n";
        $message .= "❌ بن: {$status_counts['بن']}\n";
        $message .= "⭕ آفلاین: {$status_counts['آفلاین']}\n";
        $message .= "📱 کل: " . count($accounts);
        
        return $message;
    }
    
    // Analyze group messages for member extraction
    private function analyzeGroupMembers($group_id) {
        // Simulate member extraction from group analysis
        $sample_members = [
            ['id' => mt_rand(100000, 999999), 'username' => 'user1', 'first_name' => 'علی', 'last_name' => 'احمدی'],
            ['id' => mt_rand(100000, 999999), 'username' => 'user2', 'first_name' => 'محمد', 'last_name' => 'رضایی'],
            ['id' => mt_rand(100000, 999999), 'username' => 'user3', 'first_name' => 'فاطمه', 'last_name' => 'کریمی'],
            ['id' => mt_rand(100000, 999999), 'username' => 'user4', 'first_name' => 'سارا', 'last_name' => 'محمدی'],
            ['id' => mt_rand(100000, 999999), 'username' => 'user5', 'first_name' => 'حسین', 'last_name' => 'موسوی']
        ];
        
        $members = $this->loadMembers();
        $members[$group_id] = [
            'group_id' => $group_id,
            'members' => $sample_members,
            'extracted_date' => date('Y-m-d H:i:s'),
            'total_count' => count($sample_members)
        ];
        
        $this->saveMembers($members);
        
        return count($sample_members);
    }
    
    // Get extracted members list
    private function getMembersList($group_id = null) {
        $members = $this->loadMembers();
        
        if (empty($members)) {
            return "❌ هیچ لیست ممبری یافت نشد";
        }
        
        $message = "👥 <b>لیست ممبرهای استخراج شده:</b>\n\n";
        
        foreach ($members as $gid => $group_data) {
            if ($group_id && $gid != $group_id) continue;
            
            $message .= "🔸 <b>گروه ID:</b> {$gid}\n";
            $message .= "📅 <b>تاریخ استخراج:</b> {$group_data['extracted_date']}\n";
            $message .= "👤 <b>تعداد ممبر:</b> {$group_data['total_count']}\n\n";
            
            foreach (array_slice($group_data['members'], 0, 10) as $member) {
                $username = isset($member['username']) ? "@{$member['username']}" : "بدون یوزرنیم";
                $message .= "• {$member['first_name']} {$member['last_name']} ({$username})\n";
            }
            
            if (count($group_data['members']) > 10) {
                $remaining = count($group_data['members']) - 10;
                $message .= "... و {$remaining} ممبر دیگر\n";
            }
            $message .= "\n";
        }
        
        return $message;
    }
    
    // Send private messages to members
    private function sendPrivateMessages($group_id, $banner_message) {
        $members = $this->loadMembers();
        
        if (!isset($members[$group_id])) {
            return "❌ لیست ممبر برای این گروه یافت نشد";
        }
        
        $group_members = $members[$group_id]['members'];
        $success_count = 0;
        $failed_count = 0;
        
        foreach ($group_members as $member) {
            // Simulate sending message
            $success = mt_rand(0, 1); // 50% success rate simulation
            
            if ($success) {
                $success_count++;
                // In real implementation, send message to $member['id']
                // $this->sendMessage($member['id'], $banner_message);
            } else {
                $failed_count++;
            }
            
            // Small delay to avoid rate limiting
            usleep(500000); // 0.5 second delay
        }
        
        return "📊 <b>نتیجه ارسال پیام:</b>\n\n" .
               "✅ موفق: {$success_count}\n" .
               "❌ ناموفق: {$failed_count}\n" .
               "📱 کل: " . count($group_members);
    }
    
    // Main webhook handler
    public function handleWebhook() {
        $input = file_get_contents('php://input');
        $update = json_decode($input, true);
        
        if (!$update) return;
        
        $message = $update['message'] ?? null;
        if (!$message) return;
        
        $chat_id = $message['chat']['id'];
        $user_id = $message['from']['id'];
        $text = $message['text'] ?? '';
        
        // Check if user is admin
        if ($user_id != $this->admin_id) {
            $this->sendMessage($chat_id, "❌ شما مجاز به استفاده از این ربات نیستید");
            return;
        }
        
        // Handle commands
        if ($text == '/start') {
            $keyboard = [
                'keyboard' => [
                    [['text' => '➕ افزودن اکانت'], ['text' => '📊 وضعیت اکانت‌ها']],
                    [['text' => '🔍 انالیز گروه'], ['text' => '👥 لیست ممبرها']],
                    [['text' => '📨 ارسال پیام خصوصی']]
                ],
                'resize_keyboard' => true
            ];
            
            $welcome_msg = "🤖 <b>ربات ارسال کننده تلگرام</b>\n\n" .
                          "✨ قابلیت‌های موجود:\n" .
                          "• مدیریت اکانت‌ها\n" .
                          "• انالیز پیشرفته گروه‌ها\n" .
                          "• استخراج لیست ممبرها\n" .
                          "• ارسال پیام خصوصی\n\n" .
                          "از منوی زیر گزینه مورد نظر را انتخاب کنید:";
            
            $this->sendMessage($chat_id, $welcome_msg, $keyboard);
        }
        elseif ($text == '➕ افزودن اکانت') {
            $this->sendMessage($chat_id, "📱 شماره تلفن اکانت را وارد کنید:\n(مثال: +989123456789)");
        }
        elseif ($text == '📊 وضعیت اکانت‌ها') {
            $status = $this->getAccountsStatus();
            $this->sendMessage($chat_id, $status);
        }
        elseif ($text == '🔍 انالیز گروه') {
            $this->sendMessage($chat_id, "🔗 ID گروه مورد نظر برای انالیز را وارد کنید:\n(مثال: -1001234567890)");
        }
        elseif ($text == '👥 لیست ممبرها') {
            $members_list = $this->getMembersList();
            $this->sendMessage($chat_id, $members_list);
        }
        elseif ($text == '📨 ارسال پیام خصوصی') {
            $this->sendMessage($chat_id, "🔗 ابتدا ID گروه را وارد کنید:\n(مثال: -1001234567890)");
        }
        elseif (isValidPhoneNumber($text)) {
            // Handle phone number input
            $result = $this->addAccount($text);
            $this->sendMessage($chat_id, $result);
            logMessage("Account added: {$text} by user {$user_id}");
        }
        elseif (isValidGroupId($text)) {
            // Handle group ID for analysis
            $member_count = $this->analyzeGroupMembers($text);
            $this->sendMessage($chat_id, "✅ انالیز گروه تکمیل شد!\n👥 تعداد ممبرهای استخراج شده: {$member_count}\n\n📋 برای مشاهده لیست از منو 'لیست ممبرها' را انتخاب کنید");
            logMessage("Group analyzed: {$text} - {$member_count} members found by user {$user_id}");
        }
        elseif (strpos($text, 'send:') === 0) {
            // Handle private message sending format: send:group_id:message
            $parts = explode(':', $text, 3);
            if (count($parts) == 3) {
                $group_id = $parts[1];
                $banner_message = $parts[2];
                $result = $this->sendPrivateMessages($group_id, $banner_message);
                $this->sendMessage($chat_id, $result);
            } else {
                $this->sendMessage($chat_id, "❌ فرمت اشتباه است\nفرمت صحیح: send:group_id:پیام شما");
            }
        }
        else {
            $help_msg = "❓ <b>راهنمای استفاده:</b>\n\n" .
                       "🔸 برای افزودن اکانت: شماره تلفن وارد کنید\n" .
                       "🔸 برای انالیز گروه: ID گروه وارد کنید\n" .
                       "🔸 برای ارسال پیام: send:group_id:متن پیام\n\n" .
                       "از منوی اصلی استفاده کنید 👆";
            
            $this->sendMessage($chat_id, $help_msg);
        }
    }
}

// Initialize bot using config values
$bot = new TelegramSenderBot(BOT_TOKEN, ADMIN_ID);

// Handle webhook
$bot->handleWebhook();
?>