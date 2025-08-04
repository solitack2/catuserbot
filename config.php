<?php
// Bot Configuration
define('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE'); // Replace with your actual bot token
define('ADMIN_ID', 123456789); // Replace with your Telegram user ID

// Database Configuration
define('DB_HOST', 'localhost');
define('DB_NAME', 'telegram_bot');
define('DB_USER', 'root');
define('DB_PASS', '');

// Bot Settings
define('BOT_NAME', 'Instagram Downloader Bot');
define('MAX_DOWNLOADS_PER_DAY', 50);
define('MAX_FILE_SIZE', 50 * 1024 * 1024); // 50MB

// Create database connection
function getDB() {
    try {
        $pdo = new PDO("mysql:host=".DB_HOST.";dbname=".DB_NAME.";charset=utf8mb4", DB_USER, DB_PASS);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $pdo;
    } catch(PDOException $e) {
        error_log("Database connection failed: " . $e->getMessage());
        return false;
    }
}

// Initialize database tables
function initDB() {
    $pdo = getDB();
    if (!$pdo) return false;
    
    try {
        // Users table
        $pdo->exec("CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            downloads_today INT DEFAULT 0,
            total_downloads INT DEFAULT 0,
            is_banned BOOLEAN DEFAULT FALSE,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )");
        
        // Downloads table
        $pdo->exec("CREATE TABLE IF NOT EXISTS downloads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            url VARCHAR(500),
            file_type VARCHAR(50),
            file_size INT,
            download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )");
        
        // Settings table
        $pdo->exec("CREATE TABLE IF NOT EXISTS settings (
            setting_key VARCHAR(100) PRIMARY KEY,
            setting_value TEXT
        )");
        
        return true;
    } catch(PDOException $e) {
        error_log("Database initialization failed: " . $e->getMessage());
        return false;
    }
}

// Initialize database on first run
initDB();
?>