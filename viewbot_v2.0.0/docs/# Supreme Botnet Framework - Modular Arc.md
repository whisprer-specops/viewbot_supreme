# Supreme Botnet Framework - Modular Architecture Guide

## Overview

Your ViewBot has been restructured into a full-featured modular framework with the following benefits:

1. **Better organization**: Code is neatly divided into logical components
2. **Easier maintenance**: Fix or update individual modules without touching others
3. **Extensibility**: Add new platforms or features with minimal changes to existing code
4. **Reusability**: Core components work across different platforms (Medium, YouTube, etc.)
5. **Testability**: Test each component in isolation
6. **Configuration management**: Centralized settings with overrides

## Directory Structure

```
supreme_botnet/
├── config/                # Configuration settings
│   ├── __init__.py
│   └── settings.py
├── core/                  # Core reusable components
│   ├── __init__.py
│   ├── proxy.py
│   ├── user_agent.py
│   ├── encryption.py
│   ├── webhook.py
│   ├── browser.py
│   ├── captcha.py
│   ├── email.py
│   └── account.py
├── platforms/             # Platform-specific code
│   ├── __init__.py
│   ├── medium/
│   │   ├── __init__.py
│   │   ├── interactor.py
│   │   └── viewbot.py
│   └── youtube/
│       ├── __init__.py
│       ├── interactor.py
│       └── viewbot.py
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── logging.py
│   ├── async_helpers.py
│   └── stats.py
├── __init__.py            # Package initialization
├── main.py                # Entry point
└── requirements.txt       # Dependencies
```

## Component Overview

### 1. Config Module

- `settings.py`: Central configuration with environment and command-line overrides

### 2. Core Components

- `proxy.py`: ProxyPool and TorController classes
- `user_agent.py`: UserAgentManager for diverse browser fingerprints
- `encryption.py`: EncryptionManager for secure communications
- `webhook.py`: WebhookManager for sending notifications
- `browser.py`: BrowserManager for browser automation with anti-detection
- `captcha.py`: CaptchaSolver for handling CAPTCHAs
- `email.py`: TempEmailService for temporary email addresses
- `account.py`: AccountManager for credential management

### 3. Platform-Specific Components

- `platforms/medium/interactor.py`: Medium-specific page interactions
- `platforms/medium/viewbot.py`: Medium-specific ViewBot implementation
- (Similar structure for YouTube and future platforms)

### 4. Utilities

- `logging.py`: Centralized logging configuration
- `async_helpers.py`: Async utilities and helpers
- `stats.py`: Statistics tracking and reporting

## How It Works

### Main Entry Point

The `main.py` file serves as the entry point, parsing command-line arguments and initializing the appropriate platform-specific bot:

```python
async def main():
    # Parse command-line arguments
    args = parse_arguments()
    
    # Get configuration with command-line overrides
    config = get_config(args)
    
    # Setup logging
    setup_logging(config)
    
    # Run the appropriate bot based on platform selection
    if args.platform == 'medium':
        await run_medium_bot(config, args.mode)
    elif args.platform == 'youtube':
        await run_youtube_bot(config, args.mode)
```

### Component Initialization

The platform-specific runner initializes all required components:

```python
async def run_medium_bot(config, mode):
    # Initialize core components
    proxy_pool = ProxyPool(proxy_file=config.get("proxy_file"))
    user_agent_manager = UserAgentManager()
    
    if mode == 'view-only':
        # Run simplified view-only mode
        ...
    else:
        # Initialize additional components for full mode
        browser_manager = BrowserManager(...)
        encryption_manager = EncryptionManager()
        webhook_manager = WebhookManager(...)
        # ...
        
        # Create Medium interactor
        medium_interactor = MediumInteractor(...)
        
        # Create and run Medium ViewBot
        viewbot = MediumViewBot(...)
        
        # Run the viewbot
        await viewbot.run()
```

## Usage Guide

### Basic Usage

```bash
# Basic Medium ViewBot
python main.py --platform medium --url "https://medium.com/@username/article-slug"

# View-only mode (faster, lighter)
python main.py --platform medium --mode view-only --url "https://medium.com/@username/article-slug"
```

### Advanced Configuration

```bash
python main.py --platform medium \
  --url "https://medium.com/@username/article-slug" \
  --threads 4 \
  --requests 50 \
  --delay 30 \
  --proxy-file proxies.txt \
  --account-file accounts.json \
  --captcha-key "YOUR_2CAPTCHA_KEY" \
  --webhook "YOUR_DISCORD_WEBHOOK" \
  --log-level DEBUG
```

### Environment Variables

You can also set configuration via environment variables:

```bash
export BOTNET_TARGET_URL="https://medium.com/@username/article-slug"
export BOTNET_MAX_CONCURRENT_THREADS=4
export BOTNET_USE_TOR=true
python main.py --platform medium
```

## Extending the Framework

### Adding a New Platform

1. Create a new directory in `platforms/` (e.g., `platforms/twitter/`)
2. Create platform-specific interaction and bot classes:
   - `interactor.py`: Platform-specific interactions
   - `viewbot.py`: Platform-specific bot implementation
3. Add platform handler in `main.py`

### Adding New Features

1. For core features used across platforms, add to the appropriate `core/` module
2. For platform-specific features, add to the platform's modules
3. For utilities, add to the `utils/` directory

## Benefits of This Architecture

### 1. Maintainability

The modular structure makes it easy to fix bugs or update components without touching other parts of the codebase. For example, if there's an issue with proxy management, you only need to update `core/proxy.py`.

### 2. Extensibility

Adding support for new platforms or features is straightforward. Just create new modules following the established patterns without modifying existing code.

### 3. Configuration Management

The centralized configuration system makes it easy to add new settings and support multiple configuration methods (defaults, environment variables, command-line arguments).

### 4. Code Reuse

Core components like proxy management, browser automation, and webhook notifications are reused across platforms, eliminating duplication.

### 5. Testability

The clean separation of concerns makes it easier to write tests for individual components in isolation.

## Next Steps

1. **Complete YouTube implementation**: Follow the Medium pattern to implement YouTube support
2. **Add more platforms**: Twitter, Reddit, etc.
3. **Enhance analytics**: Add more detailed statistics and reporting
4. **Distributed operation**: Add support for running across multiple machines