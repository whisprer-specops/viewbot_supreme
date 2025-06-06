# decryptor_bot.py
import os
import discord
from discord.ext import commands
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import argparse
import re
import asyncio
import json

class WebhookDecryptorBot(commands.Bot):
    def __init__(self, decryption_key, salt=None, password=None, command_prefix='!'):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=command_prefix, intents=intents)
        if decryption_key:
            self.key = decryption_key.encode() if isinstance(decryption_key, str) else decryption_key
            self.cipher = Fernet(self.key)
            self.key_type = "direct"
        elif password and salt:
            self.key_type = "derived"
            self.salt = salt.encode() if isinstance(salt, str) else salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000
            )
            self.key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self.cipher = Fernet(self.key)
        else:
            raise ValueError("Either decryption_key or both password and salt must be provided")
        self.vote_callback = None  # Callback to trigger voting
        self.setup_events()

    def setup_events(self):
        @self.event
        async def on_ready():
            print(f'Bot is ready! Logged in as {self.user.name} ({self.user.id})')
            print(f'Using key type: {self.key_type}')
            print('------')

        @self.event
        async def on_message(message):
            if message.author == self.user:
                return
            await self.check_for_encrypted_content(message)
            await self.process_commands(message)

        self.add_command(commands.Command(self.decrypt_command, name="decrypt"))
        self.add_command(commands.Command(self.vote_command, name="vote"))
        self.add_command(commands.Command(self.help_command, name="help"))

    async def check_for_encrypted_content(self, message):
        encrypted_pattern = r'gAAAAA[0-9A-Za-z\-_]{50,}'
        matches = re.findall(encrypted_pattern, message.content)
        if matches:
            for encrypted in matches:
                try:
                    decrypted = self.decrypt(encrypted)
                    if "discord.com/api/webhooks" in decrypted:
                        embed = discord.Embed(
                            title="Decrypted Webhook",
                            description="Found and decrypted a webhook URL!",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Encrypted", value=f"```{encrypted[:20]}...{encrypted[-20:]}```", inline=False)
                        embed.add_field(name="Decrypted", value=f"```{decrypted}```", inline=False)
                        await message.channel.send(embed=embed)
                    else:
                        try:
                            vote_data = json.loads(decrypted)
                            if "vote_url" in vote_data and self.vote_callback:
                                embed = discord.Embed(
                                    title="Vote Instruction Decrypted",
                                    description="Decrypted voting instructions!",
                                    color=discord.Color.blue()
                                )
                                embed.add_field(name="Vote URL", value=f"```{vote_data['vote_url']}```", inline=False)
                                embed.add_field(name="Payload", value=f"```{json.dumps(vote_data.get('payload', {}))}```", inline=False)
                                await message.channel.send(embed=embed)
                                await self.vote_callback(vote_data["vote_url"], vote_data.get("payload", {}))
                            else:
                                embed = discord.Embed(
                                    title="Decrypted Content",
                                    description="Successfully decrypted, but not a webhook or vote instruction.",
                                    color=discord.Color.blue()
                                )
                                embed.add_field(name="Encrypted", value=f"```{encrypted[:20]}...{encrypted[-20:]}```", inline=False)
                                embed.add_field(name="Decrypted", value=f"```{decrypted}```", inline=False)
                                await message.channel.send(embed=embed)
                        except json.JSONDecodeError:
                            embed = discord.Embed(
                                title="Decrypted Content",
                                description="Successfully decrypted, but not a valid JSON vote instruction.",
                                color=discord.Color.blue()
                            )
                            embed.add_field(name="Encrypted", value=f"```{encrypted[:20]}...{encrypted[-20:]}```", inline=False)
                            embed.add_field(name="Decrypted", value=f"```{decrypted}```", inline=False)
                            await message.channel.send(embed=embed)
                except Exception as e:
                    continue

    async def decrypt_command(self, ctx, *, encrypted_text=None):
        if not encrypted_text:
            await ctx.send("Please provide encrypted text to decrypt. Usage: `!decrypt <encrypted_text>`")
            return
        try:
            decrypted = self.decrypt(encrypted_text)
            embed = discord.Embed(
                title="Decryption Result",
                description="Successfully decrypted the content!",
                color=discord.Color.green()
            )
            embed.add_field(name="Original", value=f"```{encrypted_text[:20]}...{encrypted_text[-20:]}```", inline=False)
            embed.add_field(name="Decrypted", value=f"```{decrypted}```", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Decryption Failed",
                description="Could not decrypt the provided text.",
                color=discord.Color.red()
            )
            embed.add_field(name="Error", value=f"```{str(e)}```", inline=False)
            await ctx.send(embed=embed)

    async def vote_command(self, ctx, *, vote_url=None):
        if not vote_url:
            await ctx.send("Please provide a vote URL. Usage: `!vote <vote_url> [payload_json]`")
            return
        try:
            payload = {}
            args = vote_url.split(" ", 1)
            vote_url = args[0]
            if len(args) > 1:
                payload = json.loads(args[1])
            if self.vote_callback:
                await self.vote_callback(vote_url, payload)
                embed = discord.Embed(
                    title="Vote Initiated",
                    description=f"Started vote boosting for {vote_url}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Vote Failed",
                    description="No vote callback registered.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        except json.JSONDecodeError as e:
            embed = discord.Embed(
                title="Vote Failed",
                description="Invalid payload JSON.",
                color=discord.Color.red()
            )
            embed.add_field(name="Error", value=f"```{str(e)}```", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Vote Failed",
                description="An error occurred while processing the vote command.",
                color=discord.Color.red()
            )
            embed.add_field(name="Error", value=f"```{str(e)}```", inline=False)
            await ctx.send(embed=embed)

    async def help_command(self, ctx):
        embed = discord.Embed(
            title="Webhook Decryptor Bot",
            description="I can decrypt encrypted webhook URLs and handle voting instructions.",
            color=discord.Color.blue()
        )
        embed.add_field(name="!decrypt <encrypted_text>", value="Decrypt the provided text", inline=False)
        embed.add_field(name="!vote <vote_url> [payload_json]", value="Initiate voting for the specified URL with optional JSON payload", inline=False)
        embed.add_field(name="!help", value="Show this help message", inline=False)
        embed.add_field(name="Automatic Detection", value="I automatically scan messages for encrypted content and try to decrypt it.", inline=False)
        await ctx.send(embed=embed)

    def decrypt(self, encrypted_message):
        if isinstance(encrypted_message, str):
            encrypted_message = encrypted_message.encode()
        return self.cipher.decrypt(encrypted_message).decode()

    def register_vote_callback(self, callback):
        """Register a callback function to handle voting instructions."""
        self.vote_callback = callback

def main():
    parser = argparse.ArgumentParser(description='Discord Webhook Decryptor Bot')
    parser.add_argument('--token', type=str, required=True, help='Discord bot token')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--key', type=str, help='Direct Fernet key for decryption')
    group.add_argument('--key-file', type=str, help='Path to file containing Fernet key')
    parser.add_argument('--password', type=str, help='Password for key derivation')
    parser.add_argument('--salt', type=str, help='Salt for key derivation')
    parser.add_argument('--prefix', type=str, default='!', help='Command prefix (default: !)')
    args = parser.parse_args()

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
    try:
        bot = WebhookDecryptorBot(
            decryption_key=decryption_key,
            password=args.password,
            salt=args.salt,
            command_prefix=args.prefix
        )
        bot.run(args.token)
    except Exception as e:
        print(f"Error starting the bot: {e}")

if __name__ == "__main__":
    main()