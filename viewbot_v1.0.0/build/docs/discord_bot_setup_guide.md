# Discord Webhook Decryptor Bot - Setup Guide

This guide will walk you through setting up and using the Discord Webhook Decryptor Bot, which can automatically decrypt your encrypted webhook messages as they arrive in your server.

## Prerequisites

1. Python 3.8 or higher
2. discord.py library: `pip install discord.py`
3. cryptography library: `pip install cryptography`
4. A Discord bot token (we'll cover how to get this)

## Step 1: Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name like "Webhook Decryptor"
3. Navigate to the "Bot" tab in the left sidebar
4. Click "Add Bot" and confirm
5. Under "Privileged Gateway Intents", enable "Message Content Intent" (this allows the bot to read messages)
6. Click "Reset Token" to get your bot token (save this securely!)
7. Under the "OAuth2" tab, select "URL Generator"
8. For scopes, select "bot"
9. For permissions, select:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
10. Copy the generated URL and open it in your browser to invite the bot to your server

## Step 2: Extract Your Encryption Key

The bot needs your encryption key to decrypt webhook messages. Use the `extract_key.py` script to get it:

```bash
# Simpler approach - just extract and create a launch script
python extract_key.py --create-launch-script

# For more options
python extract_key.py --service webhook --check-env --create-launch-script --output bot_key.txt
```

This will:
1. Look for your encryption key in `~/.supremebot/keys.json`
2. Optionally check environment variables
3. Save the key to a file and create a launch script

## Step 3: Launch the Bot

1. Edit the generated launch script to add your Discord bot token:

```bash
# Edit this line in launch_decryptor_bot.sh (or .bat on Windows)
python discord_decryptor_bot.py --token "YOUR_DISCORD_BOT_TOKEN_HERE" --key "your_encryption_key"
```

2. Run the script:

```bash
# On Linux/Mac
./launch_decryptor_bot.sh

# On Windows
launch_decryptor_bot.bat
```

## Step 4: Using the Bot

Once the bot is running and has joined your server, it will:

1. **Automatically** detect and decrypt any encrypted webhook URLs in messages
2. Respond with both the encrypted and decrypted versions
3. Let you manually decrypt content using the `!decrypt` command

### Commands

- `!decrypt <encrypted_text>` - Decrypt the provided text
- `!help` - Show help information

## Troubleshooting

### Bot Not Decrypting Messages

If the bot isn't decrypting your messages, check:

1. **Encryption Key**: Make sure you're using the correct key that was used to encrypt the webhooks
2. **Message Format**: The encrypted content should start with "gAAAAA" followed by base64-encoded content
3. **Bot Permissions**: Ensure the bot has permission to read messages in the channel
4. **Intents**: Make sure you enabled the Message Content Intent in the Discord Developer Portal

### Invalid Key Format

If you get an error about invalid key format, the key might be malformed. The key should be a URL-safe base64-encoded 32-byte value.

### Cannot Read Messages

If the bot can't read messages, make sure:
1. You enabled the Message Content Intent
2. The bot has the "Read Messages/View Channels" permission

## Running the Bot 24/7 (Optional)

For continuous operation, consider:

1. **Running on a VPS**: Use a service like DigitalOcean, AWS, or Heroku
2. **Using a process manager**: Tools like PM2 or systemd can keep the bot running
3. **Adding error handling**: Update the script to restart on crashes

```bash
# Example using PM2
npm install pm2 -g
pm2 start launch_decryptor_bot.sh --name webhook-decryptor
pm2 save
```

## Security Considerations

1. **Bot Token**: Never share your Discord bot token
2. **Encryption Key**: Keep your encryption key secure 
3. **Server Access**: Run the bot in servers where you trust all members, as the decrypted webhooks will be visible to everyone

## Going Further

You could enhance the bot to:

1. **Restrict usage**: Only respond to certain users or in specific channels
2. **Add more commands**: Like re-encrypting content or generating new keys
3. **Add logging**: Save decrypted webhooks to a file
4. **Add a database**: Store and manage multiple different encryption keys