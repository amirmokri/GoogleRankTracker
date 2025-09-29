# GoogleRankTracker

A sophisticated Python tool for tracking your website's ranking position in Google search results across multiple keywords. Built with Selenium WebDriver to bypass anti-bot measures and provide accurate, real-time ranking data.

## 🚀 Features

- **Human-like Behavior**: Uses real browser automation to avoid detection
- **Multi-language Support**: Works with Persian, English, and other languages
- **Real-time Results**: Automatically appends results to CSV as they're found
- **Accurate Ranking**: Calculates absolute ranks across multiple search pages
- **Anti-Captcha Handling**: Interactive captcha solving with clear instructions
- **Robust Error Handling**: Comprehensive retry logic and error recovery
- **Configurable Settings**: Customizable delays, timeouts, and search parameters
- **Cross-platform**: Works on Windows, macOS, and Linux

## 📋 Requirements

- Python 3.8+
- Google Chrome browser
- Internet connection

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/GoogleRankTracker.git
cd GoogleRankTracker
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python test_selenium_tracker.py
```

## 📖 Usage

### Basic Usage
```bash
python selenium_ranking_tracker.py --url yourwebsite.com
```

### Advanced Usage
```bash
python selenium_ranking_tracker.py --url yourwebsite.com --keywords custom_keywords.txt --output results.csv --max-pages 5
```

### Command Line Arguments
- `--url`: Target website URL to track (required)
- `--keywords`: Path to keywords file (default: `keywords.txt`)
- `--output`: Output CSV file path (default: `results.csv`)
- `--max-pages`: Maximum pages to search (default: 10)
- `--debug`: Enable debug logging

### Keywords File Format
Create a `keywords.txt` file with one keyword per line:
```
اتوپلاستی در کرج
جراحی بینی
لیپوساکشن
```

## 📊 Output

Results are automatically saved to a CSV file with the following columns:
- `Keyword`: The searched keyword
- `Rank`: Absolute ranking position (1, 2, 3, etc.)
- `Page`: Page number where the result appears
- `URL`: Full URL of the ranked page

Example output:
```csv
Keyword,Rank,Page,URL
اتوپلاستی در کرج,8,1,https://yourwebsite.com/otoplasty/
جراحی بینی,15,2,https://yourwebsite.com/rhinoplasty/
```

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
    "max_pages": 10,
    "min_delay": 2,
    "max_delay": 5,
    "timeout": 30,
    "max_retries": 3,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ],
    "google_base_url": "https://www.google.com/search",
    "language": "fa",
    "safe_search": "off"
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Captcha Appears
- **Solution**: The tool will pause and show instructions
- Keep the browser window visible (not minimized)
- Solve the captcha manually and press Enter to continue

#### 2. SSL/Connection Errors
- **Solution**: The tool includes SSL error handling
- Ensure stable internet connection
- Avoid VPN or proxy interference

#### 3. No Results Found
- **Check**: Verify your website URL is correct
- **Check**: Ensure keywords are relevant to your content
- **Check**: Try with `--debug` flag for detailed logs

#### 4. Chrome Driver Issues
- **Solution**: The tool auto-downloads ChromeDriver
- Ensure Chrome browser is installed and updated

### Debug Mode
Run with debug logging for detailed information:
```bash
python selenium_ranking_tracker.py --url yourwebsite.com --debug
```

## 📁 Project Structure

```
GoogleRankTracker/
├── selenium_ranking_tracker.py    # Main tracker script
├── alternative_ranking_tracker.py # Alternative implementation
├── requirements.txt               # Python dependencies
├── config.json                   # Configuration settings
├── keywords.txt                  # Keywords to track
├── test_selenium_tracker.py      # Installation test
├── test_captcha_handling.py      # Captcha test
├── install_selenium_solution.bat # Windows installer
├── install_selenium_solution.sh  # Linux/Mac installer
├── CAPTCHA_SOLUTION.md           # Captcha handling guide
├── output/                       # Results directory
│   └── result.csv               # Generated results
└── README.md                    # This file
```

## 🔒 Legal and Ethical Considerations

- **Respect robots.txt**: This tool respects Google's robots.txt
- **Rate Limiting**: Built-in delays prevent server overload
- **Terms of Service**: Ensure compliance with Google's ToS
- **Personal Use**: Intended for legitimate SEO monitoring
- **No Scraping**: Only tracks your own website's rankings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the debug logs
3. Open an issue on GitHub
4. Provide detailed error information

## 🔄 Updates

- **v1.0.0**: Initial release with Selenium-based tracking
- **v1.1.0**: Added captcha handling and improved accuracy
- **v1.2.0**: Enhanced URL matching and duplicate prevention

## 📈 Performance Tips

- **Batch Processing**: Process keywords in smaller batches for better stability
- **Nighttime Running**: Run during off-peak hours to reduce captcha frequency
- **Regular Updates**: Keep Chrome and dependencies updated
- **Monitor Resources**: Ensure sufficient RAM and CPU for browser automation

---

**Note**: This tool is for educational and legitimate SEO monitoring purposes only. Always respect website terms of service and implement appropriate rate limiting.