# YouTube Bot Module - Usage Guide

## Overview

The YouTube Bot module extends the Supreme Botnet Framework to automate interactions with YouTube videos. This module provides capabilities for:

- View count boosting
- Video liking
- Comment posting
- Channel subscribing
- Related video discovery
- Discord webhook notifications

## Key Features

### 1. Human-Like Viewing Patterns

The bot simulates realistic human viewing behavior:
- Watches a portion of videos (varies by video length)
- Random interaction timing
- Scrolling and player interactions
- View time analytics

### 2. Engagement Options

Configure engagement levels based on your needs:
- Video views only
- Views + likes
- Views + likes + comments
- Full engagement (views, likes, comments, subscribes)

### 3. Anti-Detection Measures

Multiple techniques to avoid detection:
- Browser fingerprint randomization
- Proxy rotation with health monitoring
- User agent diversity
- Canvas fingerprint poisoning
- Realistic timing and behavior

### 4. Multi-Video Mode

Automatically discover and engage with related videos:
- Queue recommended videos
- Follow YouTube's "Next" suggestions
- Build a network of engaged videos

## Usage

### Basic Usage

```bash
python main.py --platform youtube --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### View-Only Mode (Lighter, Faster)

```bash
python main.py --platform youtube --mode view-only --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Advanced Configuration

```bash
python main.py --platform youtube \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --threads 4 \
  --requests 50 \
  --delay 30 \
  --proxy-file proxies.txt \
  --account-file accounts.json \
  --captcha-key "YOUR_2CAPTCHA_KEY" \
  --webhook "YOUR_DISCORD_WEBHOOK"
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | YouTube video URL | Required |
| `--mode` | 'full' or 'view-only' | 'full' |
| `--threads` | Number of concurrent workers | 4 |
| `--requests` | Requests per thread | 20-40 (random) |
| `--delay` | Seconds between requests | 30-60 (random) |
| `--proxy-file` | Path to proxy list file | "proxies.txt" |
| `--account-file` | Path to account JSON file | None |
| `--captcha-key` | 2CAPTCHA API key | None |
| `--webhook` | Discord webhook URL | None |
| `--tor` | Use Tor for routing | False |
| `--headless` | Run browsers in headless mode | True |

## Additional YouTube-Specific Settings

These can be added to your config:

```python
# In config/settings.py
DEFAULT_CONFIG.update({
    # YouTube specifics
    "youtube_max_video_length": 600,  # Maximum seconds to watch
    "like_probability": 0.7,          # Chance to like videos
    "comment_probability": 0.3,       # Chance to comment
    "subscribe_probability": 0.1,     # Chance to subscribe
    "comment_text": "Great video! Really enjoyed this content."
})
```

## Best Practices

1. **Start slowly**: Begin with 1-2 threads to monitor performance
2. **Use diverse proxies**: Mix datacenter and residential proxies
3. **Randomize timing**: Use default random delays or increase them
4. **Monitor logs**: Check viewbot.log for issues
5. **Be cautious with subscribes**: Keep subscription rate low (5-10%)

## Example Usage Scenarios

### Scenario 1: Pure View Boosting

```bash
python main.py --platform youtube --mode view-only --url "https://www.youtube.com/watch?v=VIDEO_ID" --threads 6
```

### Scenario 2: Moderate Engagement

```bash
# Edit config/settings.py to set:
# "like_probability": 0.3, "comment_probability": 0.1, "subscribe_probability": 0.0

python main.py --platform youtube --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Scenario 3: Full Engagement Network

```bash
# This will engage with the target video and its related videos
python main.py --platform youtube --url "https://www.youtube.com/watch?v=VIDEO_ID" --threads 3
```

## Troubleshooting

### Common Issues

1. **CAPTCHA Challenges**
   - Use residential proxies
   - Configure 2CAPTCHA API key
   - Reduce thread count
   - Increase delays between requests

2. **Browser Crashes**
   - Reduce concurrent browser instances
   - Ensure enough system resources
   - Check proxy stability
   - Update chromedriver to latest version

3. **Low Success Rate**
   - Verify proxy list quality
   - Increase timeouts and delays
   - Run with `--verify-ssl false` if SSL errors occur
   - Check for YouTube UI changes that might affect selectors

4. **Engagement Failures**
   - Some videos disable comments
   - Login required for some actions
   - YouTube may rate-limit engagement actions
   - Check account status if using account-based interactions

5. **TOR Connection Issues**
   - Verify TOR service is running
   - Check TOR control port configuration
   - Try restarting TOR service
   - Consider using standard proxies if TOR is unstable

### Error Messages

| Error | Possible Cause | Solution |
|-------|----------------|----------|
| "Unable to locate element" | YouTube UI changed | Update selectors in interactor.py |
| "Proxy connection refused" | Dead proxy | Improve proxy filtering, use `--verify-proxies` |
| "RecaptchaDetected" | Bot detection triggered | Reduce activity, use 2CAPTCHA |
| "Browser initialization failed" | Resource issues | Reduce thread count, check system RAM |
| "ElementClickIntercepted" | Popup or overlay | Add wait time or JS click fallback |

## Advanced Configurations

### Custom Comment Templates

Create a file `comments.txt` with one comment per line:

```
Great video! Really enjoyed your explanation.
This is exactly what I was looking for, thanks!
Very informative content, subscribed!
```

Then update your config:

```python
# In config/settings.py
import random

with open('comments.txt', 'r') as f:
    COMMENTS = f.read().splitlines()

DEFAULT_CONFIG.update({
    "comment_text": lambda: random.choice(COMMENTS),
})
```

### Webhook Notifications

Set up Discord webhook notifications for real-time monitoring:

```bash
python main.py --platform youtube --url "..." --webhook "https://discord.com/api/webhooks/..."
```

The webhook will receive:
- Start/stop notifications
- Regular stat reports
- Error alerts
- Milestone achievements

### Account Management

For actions requiring authentication:

1. Create an accounts.json file:
```json
[
  {"username": "user1@example.com", "password": "pass1"},
  {"username": "user2@example.com", "password": "pass2"}
]
```

2. Run with account support:
```bash
python main.py --platform youtube --url "..." --account-file accounts.json
```

## Performance Optimization

### System Requirements

| Threads | Recommended RAM | CPU Cores | Network |
|---------|----------------|-----------|---------|
| 1-2 | 2GB | 2+ | 5+ Mbps |
| 3-5 | 4GB | 4+ | 10+ Mbps |
| 6-10 | 8GB+ | 8+ | 20+ Mbps |

### Resource Management

- **Browser Memory**: Each browser instance consumes ~120-200MB RAM
- **Proxy Management**: Maintain at least 2x proxies as threads
- **Disk Space**: Ensure 1GB+ free for browser cache and logs
- **CPU Usage**: High during browser initialization, moderate during running

## Security Considerations

1. **IP Protection**: Always use proxies or TOR to mask origin
2. **Account Safety**: Use dedicated accounts for automation
3. **Rate Limiting**: Respect YouTube's limits to avoid IP bans
4. **Legal Compliance**: Understand YouTube's Terms of Service
5. **Data Privacy**: Secure any stored account credentials

## Updates and Maintenance

The YouTube UI changes frequently. If you encounter selector issues:

1. Check console logs for specific element failures
2. Update selectors in `interactor.py`
3. Test with `--debug` flag for verbose logging
4. Consider contributing fixes back to the project

## Command Reference

```
YouTubeBot Module Commands:
  --platform youtube       Specify YouTube platform
  --url URL                YouTube video URL
  --mode {full,view-only}  Interaction mode
  --threads THREADS        Concurrent worker threads
  --requests REQUESTS      Requests per thread
  --delay DELAY            Seconds between requests
  --proxy-file FILE        Path to proxy list
  --account-file FILE      Path to account credentials
  --captcha-key KEY        2CAPTCHA API key
  --webhook URL            Discord webhook URL
  --tor                    Use Tor for routing
  --headless               Run browsers headlessly
  --debug                  Enable verbose debug logging
  --verify-proxies         Test proxies before using
  --verify-ssl {true,false} Enable/disable SSL verification
  --stats-interval SECONDS Time between stat reports
  --max-duration SECONDS   Maximum runtime duration
```

## Logging and Analytics

The bot automatically logs detailed statistics to:
- Console output
- viewbot.log file
- Discord webhook (if configured)

Key metrics tracked:
- Views, likes, comments, and subscribes
- Success rates and hourly performance
- Proxy health and efficiency
- Error rates and types

---

## Disclaimer

This tool is provided for educational and research purposes only. The authors do not endorse or encourage:

1. Violation of YouTube's Terms of Service
2. Artificial manipulation of video metrics
3. Spam, harassment, or any abusive behavior

Users assume all responsibility for how this software is deployed and any consequences thereof.

---

*Last updated: May 2025*