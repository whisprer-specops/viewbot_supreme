# 🤖 SUPREME BOTNET FRAMEWORK
# Complete User Guide & Documentation

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Core Features & Capabilities](#core-features--capabilities)
3. [Architecture Overview](#architecture-overview)
4. [Installation & Setup](#installation--setup)
5. [Medium ViewBot Implementation](#medium-viewbot-implementation)
6. [YouTube Bot Implementation](#youtube-bot-implementation)
7. [Advanced Features](#advanced-features)
8. [Proxy Management](#proxy-management)
9. [CAPTCHA Handling](#captcha-handling)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Best Practices & Ethical Considerations](#best-practices--ethical-considerations)
12. [Future Development Ideas](#future-development-ideas)

---

## Introduction

The Supreme Botnet Framework is a comprehensive, highly configurable system designed for automated interactions with web platforms. The framework provides both general and platform-specific capabilities, with current implementations focusing on Medium and YouTube.

This guide documents the complete system architecture, implementation details, usage instructions, and troubleshooting guidelines to help you understand and effectively use the framework.

---

## Core Features & Capabilities

### General Capabilities
- **Modular Architecture**: Class-based components with clear separation of concerns
- **Multi-Platform Support**: Currently includes Medium and YouTube implementations
- **Advanced Proxy Management**: Weighted rotation, failure tracking, and performance metrics
- **Asynchronous Processing**: Efficient resource usage with parallel operations
- **Human Behavior Simulation**: Realistic timing, scrolling, and interaction patterns
- **Anti-Detection Measures**: Browser fingerprint randomization and stealth techniques

### Medium-Specific Features
- **View Boosting**: Efficiently generate view counts on articles
- **Engagement Simulation**: Clapping, commenting, and author following
- **Paywall Bypass**: Multiple methods including Freedium and email-based login
- **Article Discovery**: Finding and queuing related articles

### YouTube-Specific Features
- **View Generation**: Video view count boosting
- **Engagement Actions**: Like videos and leave comments
- **Next Video Navigation**: Automated discovery of related content
- **Webhook Notifications**: Track bot activities via Discord integration

---

## Architecture Overview

The framework follows a modular architecture with several key components:

### Core Components
- **ProxyPool**: Manages and rotates IP addresses with health tracking
- **UserAgentManager**: Provides diverse browser fingerprints
- **WebhookManager**: Sends encrypted operational notifications
- **EncryptionManager**: Secures sensitive communications

### Platform-Specific Components
- **MediumInteractor**: Handles Medium-specific page interactions
- **BrowserManager**: Configures and manages browser instances
- **TempEmailService**: Provides disposable email addresses for authentication
- **YouTubeInteractor**: Manages YouTube-specific actions

### Worker System
- **Asynchronous Workers**: Handle concurrent operations
- **Specialized Workers**: View-only vs. full interaction capabilities
- **Task Coordination**: Balances resource usage and platform load

---

## Installation & Setup

### Requirements
```
aiohttp==3.9.5
beautifulsoup4==4.12.3
cryptography==42.0.8
markovify==0.9.4
requests==2.32.3
selenium==4.23.1
stem==1.8.2
websockets==12.0
argparse==1.4.0
async-timeout==4.0.3
certifi==2024.2.2
charset-normalizer==3.3.2
idna==3.6
multidict==6.0.5
pyOpenSSL==24.0.0
soupsieve==2.5
urllib3==2.2.0
yarl==1.9.4
webdriver-manager==4.0.1
```

### Basic Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/supreme-botnet.git
   cd supreme-botnet
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your proxies**
   Create a `proxies.txt` file with one proxy per line:
   ```
   http://5.45.126.128:8080
   http://8.137.13.191:8081
   http://8.209.255.13:3128
   ...
   ```

4. **Set up accounts (optional)**
   Create an `accounts.json` file:
   ```json
   [
     {"username": "user1@example.com", "password": "password1"},
     {"username": "user2@example.com", "password": "password2"}
   ]
   ```

5. **Configure for Tor (optional)**
   Ensure Tor is installed and running on port 9050.

---

## Medium ViewBot Implementation

### Quick Start

#### View-Only Mode (Lightweight)
For quick view boosting without full browser interaction:

```bash
python ultra-simple-viewbot.py
```

This provides a fast, reliable way to boost view counts without browser automation.

#### Full Interaction Mode
For complete engagement (views, claps, comments):

```bash
python supreme-viewbot-v0.7.1.py --url "https://medium.com/@username/article-slug" --threads 4
```

### Advanced Configuration

```bash
python supreme-viewbot-v0.7.1.py \
  --url "https://medium.com/@username/article-slug" \
  --threads 4 \
  --requests 50 \
  --delay 30 \
  --captcha-key "YOUR_2CAPTCHA_API_KEY" \
  --webhook "YOUR_DISCORD_WEBHOOK_URL" \
  --proxy-file "proxies.txt" \
  --account-file "accounts.json" \
  --log-level "INFO" \
  --no-freedium
```

### Available Parameters

| Parameter         | Description                   | Default       |
|-------------------|-------------------------------|---------------|
| `--url`           | Target Medium article URL     | Required      |
| `--threads`       | Number of concurrent workers  | 4             |
| `--requests`      | Requests per thread           | 20-40 (random)|
| `--delay`         | Seconds between requests      | 30-60 (random)|
| `--captcha-key`   | 2CAPTCHA API key              | None          |
| `--webhook`       | Discord webhook URL           | None          |
| `--proxy-file`    | Path to proxy list file       | "proxies.txt" |
| `--account-file`  | Path to account JSON file     | None          |
| `--log-level`     | Logging detail level          | "INFO"        |
| `--tor`           | Use Tor for routing           | False         |
| `--no-freedium`   | Disable Freedium for paywall bypass | False   |
| `--view-only`     | Only send view requests       | False         |
| `--headless`      | Run browsers in headless mode | True          |

---

## YouTube Bot Implementation

### Quick Start

```bash
python youtube-bot.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --threads 5
```

### Features

- View generation
- Video liking
- Comment posting
- Next video navigation
- Discord webhook notifications

### Configuration

Customize the YouTube bot through the configuration section:

```python
# Configuration
VIDEO_URL = "https://www.youtube.com/watch?v=your_video_id"
WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
CAPTCHA_API_KEY = 'your_2captcha_api_key'
NUM_THREADS = 10  # Number of concurrent threads
COMMENT_TEXT = "Great video! Keep up the good work!"  # The comment to post
```

### Interaction Process

1. **Visit Video**: The bot opens the specified YouTube video
2. **Handle CAPTCHA**: Solves any CAPTCHAs that appear using 2CAPTCHA
3. **Next Video**: Navigates to the next recommended video
4. **Like Video**: Clicks the like button on the new video
5. **Comment**: Posts a comment on the video
6. **Send Notification**: Sends a webhook to Discord with the new URL

---

## Advanced Features

### 1. Proxy Management

The framework includes a sophisticated proxy management system:

```python
class ProxyPool:
    def __init__(self, proxy_file=None, max_failures=3):
        self.proxies = []
        self.max_failures = max_failures
        self.lock = threading.Lock()
        
        # Load proxies from file or use defaults
        if proxy_file and os.path.exists(proxy_file):
            self.load_from_file(proxy_file)
        
        # Pre-validate proxies asynchronously
        threading.Thread(target=self._prevalidate_proxies).start()
```

Key proxy features:
- **Pre-validation**: Tests proxies before use
- **Weight-based selection**: More reliable proxies get higher selection probability
- **Failure tracking**: Automatically removes consistently failing proxies
- **Performance metrics**: Tracks success rates for each proxy
- **Multiple protocols**: Supports HTTP, HTTPS, SOCKS4, and SOCKS5
- **Thread safety**: Proper locking for concurrent access

### 2. Human-Like Behavior Simulation

The framework simulates realistic human behavior:

```python
def simulate_human_reading(self, driver, article_length=None):
    """Simulate realistic human reading patterns."""
    # Get scroll height
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    
    # Calculate read time based on article length
    words = article_length // 5  # Approx 5 chars per word
    read_time = words / random.uniform(200, 300)  # Random WPM
    
    # Add randomness (±20%)
    read_time = read_time * random.uniform(0.8, 1.2)
    
    # Divide scroll height into random segments
    segments = random.randint(5, 15)
    
    # Scroll through with random pauses, occasional backtracking
    # ...
```

Human-like features include:
- **Variable reading speeds**: Based on content length and randomization
- **Realistic scrolling**: Non-linear progression with occasional backtracking
- **Attention simulation**: Longer pauses at interesting content
- **Natural typing**: Varied keystroke timing for comments
- **Randomized action ordering**: Varied sequence of interactions

### 3. Anti-Detection Measures

The framework implements several techniques to avoid detection:

```python
def _apply_enhanced_stealth_js(self, driver):
    """Apply advanced JavaScript-based stealth techniques."""
    # Mask WebDriver presence
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Various fingerprint modifications
        // ...
    """)
```

Anti-detection features include:
- **WebDriver hiding**: Removes automation indicators
- **Canvas fingerprint poisoning**: Subtly alters fingerprinting data
- **Hardware concurrency spoofing**: Randomizes CPU core count
- **Plugin and MIME type simulation**: Adds realistic browser plugins
- **Screen properties randomization**: Small variations in dimensions
- **Browser language customization**: Region-appropriate settings

### 4. Asynchronous Processing

The framework uses Python's asyncio for efficient processing:

```python
async def main(self):
    """Main entry point for the ViewBot."""
    # Start background tasks
    tasks = []
    
    # Start view workers
    view_workers = self.config["max_concurrent_threads"]
    for _ in range(view_workers):
        tasks.append(asyncio.create_task(self.view_worker()))
        
    # Start interaction workers
    interaction_workers = max(1, view_workers // 3)
    for _ in range(interaction_workers):
        tasks.append(asyncio.create_task(self.interaction_worker()))
    
    # Start stats reporter
    tasks.append(asyncio.create_task(self.stats_reporter()))
    
    # Wait for all tasks
    await asyncio.gather(*tasks)
```

Async features include:
- **Worker specialization**: Dedicated view vs. interaction workers
- **Resource efficiency**: Non-blocking I/O operations
- **Task coordination**: Proper handling of shared resources
- **Progress monitoring**: Real-time statistics gathering
- **Graceful shutdown**: Proper task cancellation

---

## Proxy Management

### Proxy Types
The framework supports multiple proxy types:
- **HTTP/HTTPS**: Standard web proxies
- **SOCKS4/SOCKS5**: Support for socket-level proxying
- **Authenticated**: Username/password protection
- **Rotating**: IP address changes on each request

### Proxy Format
Each proxy should be listed in `proxies.txt` with the format:
```
http://host:port
http://username:password@host:port
socks5://host:port
```

### Best Practices
1. **Mix proxy types**: Combine datacenter, residential, and mobile proxies
2. **Geographical diversity**: Use proxies from different regions
3. **Rotation timing**: Avoid changing IPs too frequently (suspicious)
4. **Quality over quantity**: A few reliable proxies beat many unreliable ones
5. **Validate regularly**: Test proxies before main operations

### Recommended Proxy Sources

#### Free Options:
- ProxyScrape: https://proxyscrape.com/free-proxy-list
- Free-Proxy-List: https://free-proxy-list.net/
- Geonode: https://geonode.com/free-proxy-list/

#### Paid Services (More Reliable):
- SmartProxy: Residential proxies ($75/5GB)
- Bright Data: Datacenter proxies ($50/month)
- Oxylabs: Residential proxies ($15/GB)

---

## CAPTCHA Handling

The framework includes integration with 2CAPTCHA for solving CAPTCHAs:

### Setup
1. **Sign up for 2CAPTCHA**: Visit 2captcha.com and create an account
2. **Get API Key**: After signing up, you'll receive an API key
3. **Add to configuration**: Set the `captcha_api_key` parameter

### Implementation

```python
class CaptchaSolver:
    def __init__(self, api_key):
        self.api_key = api_key
        
    def solve_recaptcha(self, site_key, page_url, timeout=300):
        # Submit CAPTCHA to service
        payload = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        
        # Get solution (with timeout handling)
        # ...
        
    def apply_solution(self, driver, solution):
        # Apply the solution to the page
        driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";')
        driver.execute_script("___grecaptcha_cfg.clients[0].Y.Y.callback('" + solution + "')")
```

### Features
- **Multiple CAPTCHA types**: Supports reCAPTCHA v2/v3, hCaptcha
- **Timeout handling**: Proper timeouts with exponential backoff
- **Error recovery**: Graceful handling of service failures
- **JavaScript injection**: Clean solution application without clicking
- **Verification**: Confirms solution was properly applied

---

## Troubleshooting Guide

### Common Issues & Solutions

#### 1. Browser Timeouts
```
ERROR: Error interacting with article: Message: timeout: Timed out receiving message from renderer: -0.004
```

**Solutions:**
- ✅ **Increase browser timeout** in CONFIG (now set to 90 seconds)
- ✅ **Disable Freedium** temporarily (it's causing most timeouts)
- ✅ **Add browser stability options** (added in improved browser setup)
- ✅ **Switch to eager page loading** instead of complete page loading
- 🔄 **Reduce concurrent browser instances** to 3-4 max

#### 2. Proxy Connection Failures
```
ERROR: Error sending view request: [WinError 64] The specified network name is no longer available
```

**Solutions:**
- ✅ **Pre-validate proxies** before use (implemented in improved proxy handling)
- ✅ **Increase proxy cooldown time** from 5s to 10s between uses
- ✅ **Disable SSL verification** for problematic proxies
- ✅ **Better proxy error handling** with exponential backoff
- 🔄 **Consider using a different proxy provider** - many proxies appear unreliable

#### 3. SSL Certificate Errors
```
ERROR: Error sending view request: Cannot connect to host medium.com:443 ssl:True [SSLCertVerificationError]
```

**Solutions:**
- ✅ **Disable SSL verification** with `ssl=False` option
- ✅ **Add Chrome options** to ignore certificate errors
- ✅ **Use HTTP instead of HTTPS** for proxy connections where possible

#### 4. Browser Launch Failures
```
ERROR: Failed to create browser
```

**Solutions:**
- **Close all Chrome instances**
  ```bash
  # Windows
  taskkill /F /IM chrome.exe
  
  # Mac/Linux
  pkill -f chrome
  ```
- **Try ultra-simple-viewbot.py** as a fallback (no browser needed)
- **Explicitly install chromedriver**
  ```bash
  pip uninstall webdriver-manager
  pip install webdriver-manager==3.8.5
  ```
- **Reinstall dependencies**
  ```bash
  pip install -r requirements.txt --force-reinstall
  ```

### Testing Approach

When troubleshooting, follow this step-by-step approach:

1. **Start with the simple view-only script first**
   - This isolates view boosting from browser automation
   - Helps identify if proxy issues are the main problem

2. **Test a single browser interaction manually**
   - Run with `--headless=false` to see what's happening
   - Look for specific page elements that might be causing timeouts

3. **Gradually scale up thread count**
   - Start with 1-2 threads until you confirm stability
   - Increase by 1 thread at a time while monitoring

4. **Monitor CPU and memory usage**
   - Browser automation is resource-intensive
   - Ensure you're not overloading your system

---

## Best Practices & Ethical Considerations

### Technical Best Practices

1. **Start small and scale gradually** - Begin with 3-4 threads and increase if stable
2. **Use diverse proxy sources** - Mix datacenter, residential, and mobile proxies
3. **Vary interaction patterns** - Don't always perform the same actions (clap, comment, follow)
4. **Monitor system logs** - Check viewbot.log regularly for issues
5. **Randomize timing** - Avoid sending requests at exactly the same intervals
6. **Respect platform limits** - Take breaks between intensive operations
7. **Use view-only mode for initial testing** - Validate proxy setup before full interactions

### Ethical Considerations

Botnet technology can be used for various purposes. Here's an overview of ethical applications:

#### Benign and Ethical Uses:

- **Automated Testing and Load Testing**:
  - Simulate multiple users interacting with your website to test performance
  - Ensure your services can handle high traffic without crashing
- **Data Scraping and Web Crawling**:
  - Collect data from websites for research purposes (with permission)
  - Build aggregators or comparative services (respecting robots.txt)
- **Content Moderation and Monitoring**:
  - Monitor forums or communities for inappropriate content
  - Automatically enforce community standards
- **Education and Research**:
  - Learn about automation, networking, and web technologies
  - Research defensive measures against malicious bots
- **Marketing and Promotion**:
  - Generate initial visibility for legitimate content
  - Simulate early adoption to overcome cold-start problems

#### Questionable or Harmful Uses (to avoid):

- Artificially manipulating metrics for deception
- Overwhelming servers or services
- Circumventing platform terms of service
- Generating fake engagement for compensation
- Creating misleading impressions of popularity

Always consider the impact of your actions and respect the platforms and communities you interact with.

---

## Future Development Ideas

### 1. Enhanced Capabilities
- **Distributed Operation**: Run across multiple machines for scale
- **Machine Learning Integration**: Smarter interaction decisions
- **Voice/Video Support**: Handle multimedia content interactions
- **More Platforms**: Add support for Twitter, Reddit, Facebook, etc.
- **Content Generation**: AI-powered comments and responses

### 2. Technical Improvements
- **Docker Containerization**: Easy deployment and scaling
- **Proxy Auto-Discovery**: Find and validate proxies automatically
- **Cloud-Based Operation**: AWS/GCP/Azure deployment options
- **Real-Time Dashboard**: Web interface for monitoring and control
- **API Integration**: Direct platform API usage where available

### 3. Security Enhancements
- **Better Stealth**: More advanced anti-detection measures
- **Transport Encryption**: Secure communications between components
- **Credential Protection**: Enhanced security for stored accounts
- **VPN Integration**: Built-in VPN support for better anonymity
- **Distributed Command & Control**: Resilient C2 architecture