# STORM-COMPLIANCE Enterprise Content Protection & Compliance System

A comprehensive framework for copyright protection, Terms of Service monitoring, and compliance automation for messaging platforms.

## Features

### 🔍 **Violation Analysis Module**
- Automated content scanning using Telethon
- Pattern-based detection for copyright, fraud, spam, and violence violations
- Media analysis for images, videos, and audio files
- Configurable scanning depth and violation categories

### 📋 **Compliance Report Automation**
- Multi-session distributed reporting system
- Rate limiting with jitter to bypass anti-flood filters
- Category rotation for comprehensive coverage
- Real-time report tracking and statistics

### 🧪 **Stress Testing Framework**
- Load testing for moderation system resilience
- Distributed session simulation with realistic user behavior
- Multiple test scenarios (report flood, content injection, session rotation)
- Performance metrics and vulnerability assessment

### ⚖️ **DMCA Engine**
- Automated generation of legally compliant DMCA notices
- Template-based email system with customizable content
- Evidence package creation for legal proceedings
- Batch processing for multiple violations

## Installation

### Prerequisites
- Python 3.8+
- Telegram API credentials
- SMTP server access (for DMCA notices)

### Setup

1. **Clone and install dependencies:**
```bash
cd STORM_COMPLIANCE
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API credentials
```

3. **Create session files:**
```bash
mkdir sessions
# Add your Telegram session files (.session) to the sessions directory
```

## Usage

### Basic Commands

**Full Compliance Check:**
```bash
python main.py --channel @target_channel --action full
```

**Analyze Channel Only:**
```bash
python main.py --channel @target_channel --action analyze --limit 50
```

**Submit Compliance Reports:**
```bash
python main.py --channel @target_channel --action report
```

**Run Stress Tests:**
```bash
python main.py --channel @target_channel --action stress --test-type moderation_resilience --duration 15
```

**Generate DMCA Notices:**
```bash
python main.py --channel @target_channel --action dmca
```

### Advanced Usage

**Custom Copyright Information:**
```python
copyright_info = {
    'title': 'My Protected Content',
    'author': 'Copyright Holder',
    'registration_number': 'REG-123456',
    'publication_date': '2024-01-01'
}

sender_info = {
    'name': 'Authorized Agent',
    'email': 'agent@company.com',
    'company': 'Content Protection Agency',
    'address': '123 Copyright St, Protection City, PC 12345',
    'phone': '+1-555-123-4567'
}
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_API_ID` | Telegram API ID | Yes |
| `TELEGRAM_API_HASH` | Telegram API Hash | Yes |
| `DMCA_SENDER_EMAIL` | Email for DMCA notices | Yes |
| `DMCA_SENDER_PASSWORD` | Email password/app password | Yes |
| `SMTP_SERVER` | SMTP server address | No (default: gmail) |
| `SMTP_PORT` | SMTP port | No (default: 587) |
| `SEND_DMCA_NOTICES` | Enable DMCA sending | No (default: false) |

### Violation Categories

The system detects the following violation types:

- **Copyright**: Brand logos, official content, trademarks
- **Fraud**: Credit card numbers, crypto addresses, payment links
- **Spam**: Commercial links, promotional content, clickbait
- **Violence**: Dangerous driving, accidents, weapons content

## Output Structure

### Analysis Results
```
analysis_results/
├── channel_20240507_143022.json
└── channel_20240507_151045.json
```

### Compliance Reports
```
compliance_reports/
├── channel_20240507_143022.json
└── channel_20240507_151045.json
```

### Stress Test Results
```
stress_test_results/
├── channel_load_20240507_143022.json
└── channel_moderation_resilience_20240507_151045.json
```

### DMCA Notices
```
dmca_notices/
├── channel_20240507_143022.json
└── evidence_EVIDENCE-20240507143022.json
```

## API Reference

### ViolationAnalyzer
```python
analyzer = ViolationAnalyzer(api_id, api_hash)
results = await analyzer.analyze_channel('@channel', limit=100)
```

### ComplianceReporter
```python
reporter = ComplianceReporter(api_id, api_hash, session_files)
results = await reporter.submit_compliance_report('@channel', [1,2,3], 'copyright')
```

### StressTester
```python
tester = ModerationStressTester(config)
results = await tester.distributed_load_test('@channel', action_func, 10, 5)
```

### DMCAEngine
```python
engine = DMCAEngine(config)
results = await engine.send_dmca_notice('dmca@telegram.org', case_data)
```

## Legal Compliance

This system is designed for legitimate copyright protection and compliance purposes only. Users must:

1. **Own the copyrights** they are protecting
2. **Submit accurate information** in DMCA notices
3. **Follow platform terms** of service
4. **Comply with applicable laws** in their jurisdiction

## Rate Limiting

The system includes built-in rate limiting to prevent platform violations:

- **Minimum delay**: 30 seconds between reports
- **Maximum delay**: 300 seconds between reports  
- **Jitter factor**: 30% randomization
- **Concurrent sessions**: Configurable (default: 10)

## Security Features

- **Session isolation** between different accounts
- **User agent rotation** for web requests
- **Proxy support** for enhanced anonymity
- **Encrypted credential storage** via environment variables

## Troubleshooting

### Common Issues

**Session Authorization Failed:**
- Verify session files are valid
- Check API credentials in .env
- Ensure accounts are not banned

**Rate Limiting Errors:**
- Increase delay values in config
- Reduce concurrent sessions
- Add proxy rotation

**DMCA Email Failures:**
- Verify SMTP credentials
- Check email provider settings
- Enable app passwords for Gmail

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py --channel @target_channel --action analyze
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request with tests
4. Ensure compliance with legal requirements

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is provided for legitimate copyright protection and compliance purposes only. Users are responsible for ensuring their use complies with all applicable laws and platform terms of service. The authors accept no liability for misuse.

## Support

For technical support or questions:
- Create an issue in the repository
- Review the documentation
- Check the troubleshooting section
