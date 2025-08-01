import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import base64
from typing import Dict, List, Tuple
from database import DatabaseManager
import pandas as pd
from collections import defaultdict

class AdvancedAnalytics:
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_detailed_stats(self, days: int = 30) -> Dict:
        """Get detailed statistics for specified period"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Overall statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    COUNT(DISTINCT target_user_id) as unique_recipients,
                    COUNT(DISTINCT account_id) as active_accounts
                FROM messages 
                WHERE created_at >= date('now', '-{} days')
            '''.format(days))
            
            overall_stats = cursor.fetchone()
            
            # Daily message distribution
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM messages 
                WHERE created_at >= date('now', '-{} days')
                GROUP BY DATE(created_at)
                ORDER BY date
            '''.format(days))
            
            daily_stats = cursor.fetchall()
            
            # Hourly distribution
            cursor.execute('''
                SELECT 
                    strftime('%H', created_at) as hour,
                    COUNT(*) as count
                FROM messages 
                WHERE created_at >= date('now', '-{} days')
                GROUP BY strftime('%H', created_at)
                ORDER BY hour
            '''.format(days))
            
            hourly_stats = cursor.fetchall()
            
            # Account performance
            cursor.execute('''
                SELECT 
                    a.phone,
                    a.first_name,
                    COUNT(m.id) as total_sent,
                    SUM(CASE WHEN m.status = 'sent' THEN 1 ELSE 0 END) as successful,
                    ROUND(
                        (SUM(CASE WHEN m.status = 'sent' THEN 1 ELSE 0 END) * 100.0 / COUNT(m.id)), 2
                    ) as success_rate
                FROM accounts a
                LEFT JOIN messages m ON a.id = m.account_id 
                WHERE m.created_at >= date('now', '-{} days') OR m.created_at IS NULL
                GROUP BY a.id
                ORDER BY total_sent DESC
            '''.format(days))
            
            account_performance = cursor.fetchall()
            
            # Error analysis
            cursor.execute('''
                SELECT 
                    error_message,
                    COUNT(*) as count
                FROM messages 
                WHERE status = 'failed' 
                AND created_at >= date('now', '-{} days')
                AND error_message IS NOT NULL
                GROUP BY error_message
                ORDER BY count DESC
                LIMIT 10
            '''.format(days))
            
            error_analysis = cursor.fetchall()
            
            return {
                'overall': overall_stats,
                'daily': daily_stats,
                'hourly': hourly_stats,
                'accounts': account_performance,
                'errors': error_analysis
            }
    
    def generate_chart(self, chart_type: str, days: int = 7) -> io.BytesIO:
        """Generate chart and return as BytesIO object"""
        plt.style.use('default')
        plt.rcParams['font.family'] = 'Arial'
        
        stats = self.get_detailed_stats(days)
        
        if chart_type == 'daily_messages':
            return self._create_daily_chart(stats['daily'])
        elif chart_type == 'hourly_distribution':
            return self._create_hourly_chart(stats['hourly'])
        elif chart_type == 'account_performance':
            return self._create_account_chart(stats['accounts'])
        elif chart_type == 'success_rate':
            return self._create_success_rate_chart(stats['daily'])
        else:
            return None
    
    def _create_daily_chart(self, daily_stats: List[Tuple]) -> io.BytesIO:
        """Create daily messages chart"""
        if not daily_stats:
            return None
        
        dates = [datetime.strptime(stat[0], '%Y-%m-%d') for stat in daily_stats]
        total_messages = [stat[1] for stat in daily_stats]
        successful_messages = [stat[2] for stat in daily_stats]
        failed_messages = [stat[3] for stat in daily_stats]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(dates, total_messages, label='Total Messages', linewidth=2, marker='o')
        ax.plot(dates, successful_messages, label='Successful', linewidth=2, marker='s', color='green')
        ax.plot(dates, failed_messages, label='Failed', linewidth=2, marker='^', color='red')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Messages')
        ax.set_title('Daily Message Statistics')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_hourly_chart(self, hourly_stats: List[Tuple]) -> io.BytesIO:
        """Create hourly distribution chart"""
        if not hourly_stats:
            return None
        
        hours = [int(stat[0]) for stat in hourly_stats]
        counts = [stat[1] for stat in hourly_stats]
        
        # Fill missing hours with 0
        all_hours = list(range(24))
        hour_counts = [0] * 24
        
        for hour, count in zip(hours, counts):
            hour_counts[hour] = count
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars = ax.bar(all_hours, hour_counts, color='skyblue', alpha=0.7)
        
        # Highlight peak hours
        max_count = max(hour_counts)
        for i, (hour, count) in enumerate(zip(all_hours, hour_counts)):
            if count == max_count:
                bars[i].set_color('orange')
        
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Number of Messages')
        ax.set_title('Hourly Message Distribution')
        ax.set_xticks(all_hours)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_account_chart(self, account_stats: List[Tuple]) -> io.BytesIO:
        """Create account performance chart"""
        if not account_stats:
            return None
        
        # Take top 10 accounts
        account_stats = account_stats[:10]
        
        phones = [stat[0][-4:] if stat[0] else f"User {i+1}" for i, stat in enumerate(account_stats)]
        total_sent = [stat[2] or 0 for stat in account_stats]
        successful = [stat[3] or 0 for stat in account_stats]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Messages sent chart
        ax1.barh(phones, total_sent, color='lightblue', alpha=0.7)
        ax1.set_xlabel('Total Messages Sent')
        ax1.set_title('Messages Sent by Account')
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Success rate chart
        success_rates = [stat[4] or 0 for stat in account_stats]
        colors = ['green' if rate >= 80 else 'orange' if rate >= 60 else 'red' for rate in success_rates]
        ax2.barh(phones, success_rates, color=colors, alpha=0.7)
        ax2.set_xlabel('Success Rate (%)')
        ax2.set_title('Success Rate by Account')
        ax2.grid(True, alpha=0.3, axis='x')
        ax2.set_xlim(0, 100)
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_success_rate_chart(self, daily_stats: List[Tuple]) -> io.BytesIO:
        """Create success rate over time chart"""
        if not daily_stats:
            return None
        
        dates = [datetime.strptime(stat[0], '%Y-%m-%d') for stat in daily_stats]
        success_rates = []
        
        for stat in daily_stats:
            total = stat[1]
            successful = stat[2]
            rate = (successful / total * 100) if total > 0 else 0
            success_rates.append(rate)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(dates, success_rates, linewidth=3, marker='o', markersize=8, color='green')
        ax.fill_between(dates, success_rates, alpha=0.3, color='lightgreen')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Success Rate (%)')
        ax.set_title('Message Success Rate Over Time')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        
        # Add average line
        avg_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        ax.axhline(y=avg_rate, color='red', linestyle='--', alpha=0.7, 
                  label=f'Average: {avg_rate:.1f}%')
        ax.legend()
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def get_performance_report(self, days: int = 7) -> str:
        """Generate text performance report"""
        stats = self.get_detailed_stats(days)
        
        overall = stats['overall']
        
        if not overall or overall[0] == 0:
            return "📊 **گزارش عملکرد**\n\nهیچ داده‌ای برای نمایش یافت نشد."
        
        total_messages = overall[0]
        successful = overall[1]
        failed = overall[2]
        unique_recipients = overall[3]
        active_accounts = overall[4]
        
        success_rate = (successful / total_messages * 100) if total_messages > 0 else 0
        
        report = f"""
📊 **گزارش عملکرد ({days} روز گذشته)**

📈 **آمار کلی:**
• کل پیام‌ها: {total_messages:,}
• موفق: {successful:,} ({success_rate:.1f}%)
• ناموفق: {failed:,}
• گیرندگان منحصر به فرد: {unique_recipients:,}
• اکانت‌های فعال: {active_accounts}

"""
        
        # Top performing accounts
        if stats['accounts']:
            report += "🏆 **بهترین اکانت‌ها:**\n"
            for i, account in enumerate(stats['accounts'][:3], 1):
                phone = account[0]
                name = account[1] or 'بدون نام'
                total = account[2] or 0
                rate = account[4] or 0
                report += f"{i}. {name} ({phone[-4:]}): {total} پیام، {rate:.1f}% موفقیت\n"
        
        # Common errors
        if stats['errors']:
            report += "\n⚠️ **خطاهای متداول:**\n"
            for error in stats['errors'][:3]:
                report += f"• {error[0]}: {error[1]} بار\n"
        
        return report
    
    def get_recommendations(self) -> List[str]:
        """Get performance improvement recommendations"""
        stats = self.get_detailed_stats(30)
        recommendations = []
        
        overall = stats['overall']
        if not overall or overall[0] == 0:
            return ["ابتدا پیام‌هایی ارسال کنید تا بتوانیم توصیه‌هایی ارائه دهیم."]
        
        success_rate = (overall[1] / overall[0] * 100) if overall[0] > 0 else 0
        
        if success_rate < 70:
            recommendations.append("🔸 نرخ موفقیت پایین است. بررسی کنید که آیا اکانت‌ها محدود شده‌اند.")
        
        if success_rate > 90:
            recommendations.append("🔸 عملکرد عالی! می‌توانید حجم ارسال را افزایش دهید.")
        
        # Check for flood errors
        flood_errors = sum(1 for error in stats['errors'] if 'flood' in error[0].lower())
        if flood_errors > 0:
            recommendations.append("🔸 خطاهای Flood شناسایی شد. تاخیر بین پیام‌ها را افزایش دهید.")
        
        # Check account distribution
        if len(stats['accounts']) == 1:
            recommendations.append("🔸 تنها یک اکانت دارید. افزودن اکانت‌های بیشتر عملکرد را بهبود می‌بخشد.")
        
        # Check hourly distribution
        if stats['hourly']:
            peak_hour = max(stats['hourly'], key=lambda x: x[1])[0]
            recommendations.append(f"🔸 بیشترین فعالیت در ساعت {peak_hour} است. برای بهینه‌سازی از این ساعت استفاده کنید.")
        
        if not recommendations:
            recommendations.append("🔸 عملکرد شما بسیار خوب است! به همین روند ادامه دهید.")
        
        return recommendations