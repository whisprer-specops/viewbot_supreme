# Supreme ViewBot v0.7.1 - Improvements & Usage Guide

## Key Improvements

### 1. Modular Architecture
The code has been completely restructured with a modular, object-oriented approach:
- **Class-based components** for better organization and maintainability
- **Separation of concerns** between proxy management, browser control, interaction logic, etc.
- **Configurable parameters** via both config dictionary and command-line arguments

### 2. Enhanced Proxy Management
- **Weighted rotation** with dynamic adjustment based on success/failure rates
- **Failure tracking** with automatic removal of consistently failing proxies
- **Performance metrics** for monitoring proxy health
- **Thread-safe implementation** with proper locking mechanisms

### 3. Advanced Browser Automation
- **Anti-detection measures** to avoid bot detection:
  - WebDriver flags removal
  - Canvas fingerprint poisoning
  - Custom user agent and browser properties
  - Randomized behavior patterns
- **Human-like interaction simulation**:
  - Variable reading speeds based on content length
  - Realistic scrolling patterns with occasional backtracking
  - Random pauses to simulate human attention patterns
  - Natural typing pace for comments

### 4. Asynchronous Processing
- **Fully async implementation** using Python's asyncio
- **Parallel processing** for different types of interactions
- **Efficient resource management** with proper task coordination
- **Separate worker types** for views vs. full browser interactions

### 5. Robust Error Handling
- **Comprehensive exception handling** throughout the codebase
- **Graceful degradation** when services fail
- **Retry mechanisms** for transient errors
- **Detailed logging** for troubleshooting

### 6. Multiple Access Methods
- **Freedium integration** for paywall bypass
- **Email-based authentication** using temporary email services
- **Account rotation** to prevent rate limiting
- **Captcha solving** integration

### 7. Stealth Improvements
- **Tor integration** for IP rotation
- **Encrypted webhook notifications** for operational security
- **Randomized delays and behaviors** to avoid pattern detection
- **Diverse referrer and request properties** to appear more legitimate

## Usage Guide

### Basic Usage

```bash
python supreme-viewbot.py --url "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d" --threads 7
```

### Advanced Configuration

```bash
python supreme-viewbot.py \
  --url "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d" \
  --threads 7 \
  --requests 67 \
  --delay 28 \
  --captcha-key "YOUR_2CAPTCHA_API_KEY" \
  --webhook "YOUR_DISCORD_WEBHOOK_URL" \
  --proxy-file "proxies.txt" \
  --account-file "accounts.json" \
  --log-level "INFO"
```

### View-Only Mode (Lightweight)

For quick view boosting without full browser interaction:

```bash
python supreme-viewbot.py --url "https://medium.com/@username/article-slug" --view-only
```

### Using Tor

```bash
python supreme-viewbot.py --url "https://medium.com/@username/article-slug" --tor
```
Note: Requires Tor to be installed and running on port 9050

### Proxy File Format
Create a text file with one proxy per line:
```
http://1.2.3.4:8080
http://user:pass@5.6.7.8:8080
socks5://9.10.11.12:1080
```

### Account File Format
Create a JSON file with account credentials:
```json
[
  {"username": "user1@example.com", "password": "password1"},
  {"username": "user2@example.com", "password": "password2"}
]
```

## Best Practices for Effective Operation

1. **Start small and scale gradually** - Begin with 3-4 threads and increase if stable
2. **Use diverse proxy sources** - Mix datacenter, residential, and mobile proxies
3. **Vary interaction patterns** - Don't always perform the same actions (clap, comment, follow)
4. **Monitor system logs** - Check viewbot.log regularly for issues
5. **Randomize timing** - Avoid sending requests at exactly the same intervals
6. **Respect platform limits** - Take breaks between intensive operations
7. **Use view-only mode for initial testing** - Validate proxy setup before full interactions

## Troubleshooting

### Common Issues

1. **All proxies failing**
   - Verify proxy format is correct
   - Check if proxies require authentication
   - Try different proxy sources

2. **CAPTCHAs appearing frequently**
   - Reduce request frequency
   - Use residential proxies instead of datacenter
   - Ensure proper 2CAPTCHA API key configuration

3. **Browser automation errors**
   - Update chromedriver to match installed Chrome version
   - Increase timeouts for slow connections
   - Add more error handling for specific site elements

4. **Account lockouts**
   - Use longer delays between account usage
   - Avoid suspicious activity patterns
   - Rotate accounts more frequently

5. **Tor connectivity issues**
   - Verify Tor service is running (`sudo service tor status`)
   - Check Tor control port configuration
   - Try adding a password for Tor controller authentication

## Security Considerations

- **Webhook encryption** protects sensitive operational data
- **No plaintext credentials** stored in the code
- **IP rotation** prevents tracking and rate limiting
- **Browser fingerprint randomization** avoids profiling

## Future Improvement Ideas

- Distributed operation across multiple machines
- Machine learning for smarter interaction patterns
- Automatic proxy sourcing and validation
- Browser fingerprint randomization library integration
- Comment generation based on article sentiment analysis