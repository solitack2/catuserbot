-- Database setup for Instagram Downloader Bot
-- Run this script in your MySQL database

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS a1156450_solitack 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Use the database
USE a1156450_solitack;

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS downloads;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS users;

-- Create users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255) NULL,
    first_name VARCHAR(255) NULL,
    last_name VARCHAR(255) NULL,
    downloads_today INT DEFAULT 0,
    total_downloads INT DEFAULT 0,
    is_banned BOOLEAN DEFAULT FALSE,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_last_activity (last_activity),
    INDEX idx_join_date (join_date),
    INDEX idx_is_banned (is_banned)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create downloads table
CREATE TABLE downloads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    url VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INT DEFAULT 0,
    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_download_date (download_date),
    INDEX idx_file_type (file_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create settings table
CREATE TABLE settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default settings
INSERT INTO settings (setting_key, setting_value) VALUES 
('bot_status', 'active'),
('maintenance_mode', 'false'),
('max_downloads_per_day', '50'),
('welcome_message', 'سلام! به ربات دانلود اینستاگرام خوش آمدید'),
('bot_version', '2.0');

-- Create a procedure to reset daily downloads (run daily)
DELIMITER //
CREATE PROCEDURE ResetDailyDownloads()
BEGIN
    UPDATE users 
    SET downloads_today = 0 
    WHERE DATE(last_activity) < CURDATE();
END //
DELIMITER ;

-- Show table structure
SHOW TABLES;
DESCRIBE users;
DESCRIBE downloads;
DESCRIBE settings;