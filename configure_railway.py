#!/usr/bin/env python3
"""
Railway Configuration Helper
This script helps you configure your WhatsApp Agent in Railway with proper environment variables.
"""

import os
import subprocess
import sys


def check_railway_cli():
    """Check if Railway CLI is installed."""
    try:
        result = subprocess.run(['railway', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Railway CLI found: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False


def configure_openai_key():
    """Interactive configuration for OpenAI API key."""
    print("\n🤖 OPENAI API KEY CONFIGURATION")
    print("=" * 50)
    
    print("To get your OpenAI API key:")
    print("1. Go to https://platform.openai.com/api-keys")
    print("2. Sign in to your OpenAI account")
    print("3. Click 'Create new secret key'")
    print("4. Give it a name (e.g., 'WhatsApp Agent')")
    print("5. Copy the key (it starts with 'sk-')")
    
    api_key = input("\nEnter your OpenAI API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⏭️  Skipped OpenAI configuration")
        return None
    
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: OpenAI API keys usually start with 'sk-'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled OpenAI configuration")
            return None
    
    return api_key


def set_railway_variable(key, value):
    """Set a Railway environment variable."""
    try:
        # Novo formato do Railway CLI
        cmd = ['railway', 'variables', '--set', f'{key}={value}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Configurado {key}")
            return True
        else:
            # Tentar formato alternativo
            try:
                cmd_alt = ['railway', 'run', '--', 'echo', f'export {key}={value}']
                result_alt = subprocess.run(cmd_alt, capture_output=True, text=True)
                print(f"⚠️  Use o Railway Dashboard para configurar {key}")
                print(f"   Valor: {value}")
                return False
            except:
                print(f"❌ Falha ao configurar {key}: {result.stderr}")
                return False
    except Exception as e:
        print(f"❌ Erro ao configurar {key}: {e}")
        return False


def list_railway_variables():
    """List current Railway environment variables."""
    try:
        result = subprocess.run(['railway', 'variables'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📋 Current Railway Variables:")
            print(result.stdout)
        else:
            print(f"❌ Failed to list variables: {result.stderr}")
    except Exception as e:
        print(f"❌ Error listing variables: {e}")


def main():
    """Main configuration function."""
    print("🚂 Railway Configuration Helper for WhatsApp Agent")
    print("=" * 60)
    
    # Check if Railway CLI is available
    if not check_railway_cli():
        print("\n❌ Railway CLI not found!")
        print("\nTo install Railway CLI:")
        print("1. Visit: https://docs.railway.app/develop/cli")
        print("2. Install the CLI for your system")
        print("3. Run: railway login")
        print("4. Run: railway link (in your project directory)")
        print("5. Run this script again")
        return
    
    # Check if we're linked to a Railway project
    try:
        result = subprocess.run(['railway', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("\n❌ Not linked to a Railway project!")
            print("\nTo link to your project:")
            print("1. cd /home/vancim/whats_agent")
            print("2. railway link")
            print("3. Select your WhatsApp Agent project")
            print("4. Run this script again")
            return
        
        print(f"✅ Connected to Railway project")
        
    except Exception as e:
        print(f"❌ Error checking Railway status: {e}")
        return
    
    # Show current variables
    list_railway_variables()
    
    # Configure OpenAI API key
    openai_key = configure_openai_key()
    
    if openai_key:
        print(f"\n🔄 Setting OPENAI_API_KEY in Railway...")
        if set_railway_variable('OPENAI_API_KEY', openai_key):
            print("✅ OpenAI API key configured successfully!")
            
            # Trigger redeploy
            redeploy = input("\n🚀 Redeploy your application now? (y/N): ").strip().lower()
            if redeploy == 'y':
                print("🔄 Triggering redeploy...")
                try:
                    result = subprocess.run(['railway', 'up', '--detach'], capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✅ Redeploy triggered successfully!")
                        print("🔍 Check your Railway dashboard for deployment status")
                    else:
                        print(f"❌ Redeploy failed: {result.stderr}")
                except Exception as e:
                    print(f"❌ Error triggering redeploy: {e}")
        else:
            print("❌ Failed to configure OpenAI API key")
    
    print("\n🎉 CONFIGURATION COMPLETE")
    print("=" * 50)
    print("Next steps:")
    print("1. Wait for Railway deployment to complete")
    print("2. Test your WhatsApp Agent with improved LLM responses")
    print("3. Monitor logs in Railway dashboard")
    
    print("\n📊 To verify configuration, run in Railway console:")
    print("python verify_database_setup.py")


if __name__ == "__main__":
    main()
