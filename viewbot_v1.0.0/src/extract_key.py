#!/usr/bin/env python3
"""
Extract encryption key from the local config for use with the Discord Decryptor Bot.
This script reads the keys from ~/.supremebot/keys.json and prints the key 
needed for the Discord bot.
"""

import os
import json
import base64
import argparse
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

def extract_key(service_name="webhook", config_dir=None, output_file=None):
    """
    Extract the encryption key for a specific service.
    
    Args:
        service_name: Service name to extract key for
        config_dir: Config directory (default: ~/.supremebot)
        output_file: Optional file to save the key to
        
    Returns:
        str: The extracted key
    """
    # Normalize service name
    service_name = service_name.upper()
    
    # Set up config directory
    if config_dir is None:
        config_dir = Path.home() / ".supremebot"
    else:
        config_dir = Path(config_dir)
        
    # Check if config directory exists
    if not config_dir.exists():
        print(f"Config directory {config_dir} does not exist.")
        return None
        
    # Check if keys file exists
    keys_file = config_dir / "keys.json"
    if not keys_file.exists():
        print(f"Keys file {keys_file} does not exist.")
        return None
        
    # Load keys
    try:
        with open(keys_file, 'r') as f:
            keys = json.load(f)
    except Exception as e:
        print(f"Error reading keys file: {e}")
        return None
        
    # Check if service key exists
    if service_name not in keys:
        print(f"No key found for service {service_name}")
        return None
        
    # Get key
    key = keys[service_name]
    
    # If output file specified, save key to file
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(key)
            print(f"Key saved to {output_file}")
        except Exception as e:
            print(f"Error saving key to file: {e}")
    
    return key

def extract_from_env_var(service_name="webhook"):
    """
    Extract key from environment variable.
    
    Args:
        service_name: Service name to extract key for
        
    Returns:
        str: The extracted key or None
    """
    env_var_name = f"SUPREME_BOT_KEY_{service_name.upper()}"
    key = os.environ.get(env_var_name)
    
    if key:
        print(f"Found key in environment variable {env_var_name}")
        return key
    else:
        print(f"No key found in environment variable {env_var_name}")
        return None

def extract_password_and_salt(service_name="webhook", config_dir=None):
    """
    For systems using password and salt, extract them.
    
    This is a simplified version - in a real system you would use 
    a consistent salt. For this example we'll use a predefined value.
    
    Args:
        service_name: Service name
        config_dir: Config directory
        
    Returns:
        tuple: (password, salt) or (None, None)
    """
    # Default password used in the EncryptionManager
    password = "supreme_botnet_secure"
    
    # Default salt (in a proper implementation, this would be stored with the data)
    salt = b'SupremeViewBot123'  # This matches our improved implementation
    
    return password, salt

def create_launch_script(key, output_file="launch_decryptor_bot.sh"):
    """
    Create a script to launch the Discord bot with the key.
    
    Args:
        key: Encryption key
        output_file: Output file name
    """
    # Determine if we're on Windows or Unix
    if os.name == 'nt':  # Windows
        script = f'@echo off\npython discord_decryptor_bot.py --token YOUR_DISCORD_BOT_TOKEN_HERE --key "{key}"\n'
        if not output_file.endswith('.bat'):
            output_file += '.bat'
    else:  # Unix-like
        script = f'#!/bin/bash\npython discord_decryptor_bot.py --token YOUR_DISCORD_BOT_TOKEN_HERE --key "{key}"\n'
        if not output_file.endswith('.sh'):
            output_file += '.sh'
    
    # Write script
    with open(output_file, 'w') as f:
        f.write(script)
    
    # Make executable on Unix
    if os.name != 'nt':
        os.chmod(output_file, 0o755)
    
    print(f"Created launch script: {output_file}")
    print("IMPORTANT: Replace YOUR_DISCORD_BOT_TOKEN_HERE with your actual Discord bot token!")

def main():
    parser = argparse.ArgumentParser(description='Extract encryption key for Discord Decryptor Bot')
    parser.add_argument('--service', type=str, default='webhook', help='Service name (default: webhook)')
    parser.add_argument('--config-dir', type=str, help='Config directory (default: ~/.supremebot)')
    parser.add_argument('--output', type=str, help='Output file to save key to')
    parser.add_argument('--create-launch-script', action='store_true', help='Create launch script for Discord bot')
    parser.add_argument('--check-env', action='store_true', help='Check environment variables too')
    parser.add_argument('--password-mode', action='store_true', help='Use password and salt mode instead of direct key')
    
    args = parser.parse_args()
    
    if args.password_mode:
        password, salt = extract_password_and_salt(args.service, args.config_dir)
        if password and salt:
            print(f"\nPassword and salt mode:")
            print(f"Password: {password}")
            print(f"Salt: {salt.decode() if isinstance(salt, bytes) else salt}")
            
            # Create launch script if requested
            if args.create_launch_script:
                script_name = "launch_decryptor_bot_password_mode.sh" if os.name != 'nt' else "launch_decryptor_bot_password_mode.bat"
                
                # Determine if we're on Windows or Unix
                if os.name == 'nt':  # Windows
                    script = f'@echo off\npython discord_decryptor_bot.py --token YOUR_DISCORD_BOT_TOKEN_HERE --password "{password}" --salt "{salt.decode() if isinstance(salt, bytes) else salt}"\n'
                else:  # Unix-like
                    script = f'#!/bin/bash\npython discord_decryptor_bot.py --token YOUR_DISCORD_BOT_TOKEN_HERE --password "{password}" --salt "{salt.decode() if isinstance(salt, bytes) else salt}"\n'
                
                # Write script
                with open(script_name, 'w') as f:
                    f.write(script)
                
                # Make executable on Unix
                if os.name != 'nt':
                    os.chmod(script_name, 0o755)
                
                print(f"Created launch script: {script_name}")
                print("IMPORTANT: Replace YOUR_DISCORD_BOT_TOKEN_HERE with your actual Discord bot token!")
                
            return
    
    # Try to extract key from file
    key = extract_key(args.service, args.config_dir, args.output)
    
    # If key not found in file and check_env is enabled, try environment variable
    if not key and args.check_env:
        key = extract_from_env_var(args.service)
    
    # If key found, create launch script if requested
    if key and args.create_launch_script:
        create_launch_script(key)
        
    if key:
        print(f"\nEncryption key: {key}")
        print("\nUse this key with the Discord bot like this:")
        print(f"python discord_decryptor_bot.py --token YOUR_DISCORD_BOT_TOKEN_HERE --key \"{key}\"")
    

if __name__ == "__main__":
    main()