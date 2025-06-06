import os
import discord
from discord.ext import commands
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import argparse
import re

# Bot class for decrypting webhooks
class WebhookDecryptorBot(commands.Bot):
    def __init__(self, decryption_key, salt=None, password=None, command_prefix='!'):
        intents = discord.Intents.default()
        intents.message_content = True  # We need to read message content
        super().__init__(command_prefix=command_prefix, intents=intents)
        
        # If direct Fernet key is provided
        if decryption_key:
            self.key = decryption_key.encode() if isinstance(decryption_key, str) else decryption_key
            self.cipher = Fernet(self.key)
            self.key_type = "direct"
        # If password and salt are provided
        elif password and salt:
            self.key_type = "derived"
            self.password = password
            self.salt = salt.encode() if isinstance(salt, str) else salt
            
            # Generate key from password and salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000
            )
            self.key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
            self.cipher = Fernet(self.key)
        else:
            raise ValueError("Either decryption_key or both password and salt must be provided")
            
        # Set up event handlers
        self.setup_events()
        
    def setup_events(self):
        @self.event
        async def on_ready():
            print(f'Bot is ready! Logged in as {self.user.name} ({self.user.id})')
            print(f'Using key type: {self.key_type}')
            print('------')
        
        @self.event
        async def on_message(message):
            # Don't respond to our own messages
            if message.author == self.user:
                return
                
            # Check for encrypted content in the message
            await self.check_for_encrypted_content(message)
            
            # Process commands
            await self.process_commands(message)
            
        # Add commands
        self.add_command(commands.Command(self.decrypt_command, name="decrypt"))
        self.add_command(commands.Command(self.help_command, name="help"))
    
    async def check_for_encrypted_content(self, message):
        """Check if message contains encrypted content and try to decrypt it"""
        # Skip messages from webhooks themselves
        if message.webhook_id:
            return
            
        # Regular pattern for base64 encoded data that might be encrypted
        encrypted_pattern = r'gAAAAA[0-9A-Za-z\-_]{50,}'
        matches = re.findall(encrypted_pattern, message.content)
        
        if matches:
            # Try to decrypt each match
            for encrypted in matches:
                try:
                    decrypted = self.decrypt(encrypted)
                    # Check if it's a valid webhook URL
                    if "discord.com/api/webhooks" in decrypted:
                        embed = discord.Embed(
                            title="Decrypted Webhook",
                            description=f"Found and decrypted a webhook URL in a message!",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Encrypted", value=f"```{encrypted[:20]}...{encrypted[-20:]}```", inline=False)
                        embed.add_field(name="Decrypted", value=f"```{decrypted}```", inline=False)
                        await message.channel.send(embed=embed)
                    else:
                        # It decrypted but isn't a webhook URL
                        embed = discord.Embed(
                            title="Decrypted Content",
                            description=f"Successfully decrypted content, but it's not a webhook URL.",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Encrypted", value=f"```{encrypted[:20]}...{encrypted[-20:]}```", inline=False)
                        embed.add_field(name="Decrypted", value=f"```{decrypted}```", inline=False)
                        await message.channel.send(embed=embed)
                except Exception as e:
                    # Could not decrypt this content
                    continue
    
    async def decrypt_command(self, ctx, *, encrypted_text=None):
        """Command to decrypt text provided by a user"""
        if not encrypted_text:
                channel = bot.get_channel(1370674932354121860)
                await channel.send("DECRYPTOR BOT: Stats incoming...' `!decrypt <encrypted_text>`")
                return

        try:
            decrypted = self.decrypt(encrypted_text)
            embed = discord.Embed(
                title="Decryption Result",
                description="Successfully decrypted the content!",
                color=discord.Color.green()
            )
            embed.add_field(name="Original", value=f"```{encrypted_text[:20]}...{encrypted_text[-20:] if len(encrypted_text) > 40 else encrypted_text[-20:]}```", inline=False)
            embed.add_field(name="Decrypted", value=f"```{decrypted}```", inline=False)
            channel = bot.get_channel(1370674932354121860)
            await channel.send("DECRYPTOR BOT: OH NOES!! I FAIL...")
        except Exception as e:
            embed = discord.Embed(
                title="Decryption Failed",
                description=f"_Could_ decrypt the provided text but no webhook URL present.",
                color=discord.Color.red()
            )
            embed.add_field(name="Error", value=f"```{str(e)}```", inline=False)
        #    await ctx.send(embed=embed)
            channel = bot.get_channel(1370674932354121860)
        await channel.send("Uh Oh Spaghetti O's - i dun a fail :<...")

    async def help_command(self, ctx):
        """Custom help command"""
        embed = discord.Embed(
            title="Webhook Decryptor Bot",
            description="I can decrypt encrypted webhook URLs and other Fernet-encrypted content.",
            color=discord.Color.blue()
        )
        embed.add_field(name="!decrypt <encrypted_text>", value="Decrypt the provided text", inline=False)
        embed.add_field(name="!help", value="Show this help message", inline=False)
        embed.add_field(name="Automatic Detection", value="I automatically scan messages for encrypted content and try to decrypt it.", inline=False)
        await ctx.send(embed=embed)
    
    def decrypt(self, encrypted_message):
        """Decrypt a message using the configured cipher"""
        if isinstance(encrypted_message, str):
            encrypted_message = encrypted_message.encode()
        return self.cipher.decrypt(encrypted_message).decode()


def main():
    parser = argparse.ArgumentParser(description='Discord Webhook Decryptor Bot')
    parser.add_argument('--token', type=str, required=True, help='Discord bot token')
    
    # Encryption options group (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--key', type=str, help='Direct Fernet key for decryption')
    group.add_argument('--key-file', type=str, help='Path to file containing Fernet key')
    
    # Password-based options
    parser.add_argument('--password', type=str, help='Password for key derivation')
    parser.add_argument('--salt', type=str, help='Salt for key derivation')
    
    # Command prefix
    parser.add_argument('--prefix', type=str, default='!', help='Command prefix (default: !)')
    
    args = parser.parse_args()
    
    # Get encryption key
    decryption_key = None
    if args.key:
        decryption_key = args.key
    elif args.key_file:
        try:
            with open(args.key_file, 'r') as f:
                decryption_key = f.read().strip()
        except Exception as e:
            print(f"Error reading key file: {e}")
            return
    
    # Create and run the bot
    try:
        if decryption_key:
            bot = WebhookDecryptorBot(decryption_key=decryption_key, command_prefix=args.prefix)
        elif args.password and args.salt:
            bot = WebhookDecryptorBot(decryption_key=None, password=args.password, 
                                      salt=args.salt, command_prefix=args.prefix)
        else:
            print("Error: Either --key/--key-file or both --password and --salt must be provided")
            return
            
        bot.run(args.token)
    except Exception as e:
        print(f"Error starting the bot: {e}")


if __name__ == "__main__":
    main()