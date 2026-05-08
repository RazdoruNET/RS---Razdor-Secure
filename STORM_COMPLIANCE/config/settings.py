import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram API Configuration
    API_ID = os.getenv('TELEGRAM_API_ID')
    API_HASH = os.getenv('TELEGRAM_API_HASH')
    
    # Session Management
    SESSION_DIR = 'sessions'
    MAX_CONCURRENT_SESSIONS = 10
    
    # Content Analysis Settings
    SCAN_DEPTH = 100  # Number of messages to analyze
    VIOLATION_CATEGORIES = {
        'copyright': ['video', 'audio', 'image'],
        'spam': ['links', 'contact_info', 'commercial'],
        'violence': ['dangerous_driving', 'accidents', 'weapons'],
        'fraud': ['payment_links', 'card_numbers', 'scam_patterns']
    }
    
    # Rate Limiting
    MIN_DELAY = 30  # seconds
    MAX_DELAY = 300  # seconds
    JITTER_FACTOR = 0.3
    
    # DMCA Settings
    DMCA_EMAIL_TEMPLATE = 'templates/dmca_notice.html'
    DMCA_RECIPIENT = 'dmca@telegram.org'
    
    # Compliance Settings
    REPORT_CATEGORIES = ['spam', 'violence', 'copyright', 'child_abuse', 'pornography']
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/compliance_system.log'
