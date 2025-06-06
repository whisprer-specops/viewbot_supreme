🧱 1. REQUIREMENTS
Make sure you have:

Python 3.8+

pip install -r requirements.txt

Chromium/Chrome (for browser automation)

🧰 2. INSTALL DEPENDENCIES
From root folder:

bash
Copy
Edit
pip install -r requirements.txt
🔐 3. CONFIGURE YOUR WEBHOOK
A) Encrypt a Discord/Slack webhook:
bash
Copy
Edit
python config/encrypt_webhook.py
You'll be prompted:

mathematica
Copy
Edit
Enter your webhook URL to encrypt:
That creates:

config/bot_key.txt — holds Fernet key

config/webhook.enc — encrypted webhook URL

👥 4. LOAD YOUR ACCOUNTS
Edit this file:

bash
Copy
Edit
data/my_accounts.json
Format:

json
Copy
Edit
[
  {
    "email": "user@example.com",
    "password": "hunter2"
  },
  ...
]
🌐 5. SEED PROXY FILE (optional)
If you want to use a fallback source for proxies when scanning fails, populate:

bash
Copy
Edit
data/proxies.txt
Format: one proxy per line, either:

ip:port

or with auth: user:pass@ip:port

⚙️ 6. RUN THE BOT
Example: boost a Medium post using 5 workers

bash
Copy
Edit
python run.py --mode medium --target "https://medium.com/@somepost" --count 5
Or boost a YouTube video:

bash
Copy
Edit
python run.py --mode youtube --target "https://youtu.be/abc123" --count 3
Add this to skip background proxy refresh:

bash
Copy
Edit
--disable-proxy-refresh
🧠 7. BEHIND THE SCENES
ProxyManager grabs & filters fresh proxies regularly (unless disabled)

Each BotWorker:

pulls a random proxy

logs into a random account

opens a headless browser

performs claps/views

solves captchas via 2Captcha if needed

reports success/failure via webhook

💡 BONUS TIPS
Logs print to console by default — easy to tail with:

bash
Copy
Edit
python run.py ... | tee logs.txt
Extend BrowserController with more actions like:

watch_video()

clap_article()

upvote_reddit()

