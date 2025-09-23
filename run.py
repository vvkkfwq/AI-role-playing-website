#!/usr/bin/env python3
"""
AI Role-Playing Website Startup Script

This script helps initialize and run the AI role-playing application.

Usage:
    python run.py [--init] [--reset] [--sample-data]

Options:
    --init: Initialize database with preset characters (run once)
    --reset: Reset database completely (delete existing data)
    --sample-data: Create sample conversations for demonstration
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def check_requirements():
    """Check if all required packages are installed"""
    required_packages = {
        "streamlit": "streamlit",
        "openai": "openai",
        "python-dotenv": "dotenv",
        "pydantic": "pydantic"
    }

    missing_packages = []

    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} is installed")
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   • {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")

    if not env_path.exists():
        print("⚠️  .env file not found!")
        print("📝 Create .env file with:")
        print("   OPENAI_API_KEY=your_api_key_here")
        print("   OPENAI_MODEL=gpt-3.5-turbo")
        print("   APP_TITLE=AI角色扮演聊天网站")
        return False

    # Check for required variables
    with open(env_path) as f:
        content = f.read()

    if "OPENAI_API_KEY" not in content:
        print("⚠️  OPENAI_API_KEY not found in .env file!")
        return False

    return True


def init_database(reset=False, sample_data=False):
    """Initialize the database"""
    print("🔧 Initializing database...")

    cmd = ["python", "init_database.py"]

    if reset:
        cmd.append("--reset")

    if sample_data:
        cmd.append("--sample-data")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Database initialized successfully!")
            return True
        else:
            print(f"❌ Database initialization failed: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ init_database.py not found!")
        return False


def run_streamlit():
    """Run the Streamlit application"""
    print("🚀 Starting AI Role-Playing Website...")
    print("🌐 The app will open in your browser automatically.")
    print("🛑 Press Ctrl+C to stop the server")

    try:
        subprocess.run(["streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped. Goodbye!")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it with: pip install streamlit")


def main():
    parser = argparse.ArgumentParser(description="AI Role-Playing Website Startup")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--reset", action="store_true", help="Reset database")
    parser.add_argument("--sample-data", action="store_true", help="Create sample data")

    args = parser.parse_args()

    print("🎭 AI Role-Playing Website")
    print("=" * 30)

    # Check system requirements
    print("\n🔍 Checking system requirements...")

    if not check_requirements():
        sys.exit(1)

    if not check_env_file():
        sys.exit(1)

    print("✅ All requirements satisfied!")

    # Initialize database if requested or if it doesn't exist
    db_path = Path("data/roleplay.db")

    if args.init or args.reset or not db_path.exists():
        if not init_database(reset=args.reset, sample_data=args.sample_data):
            sys.exit(1)

    # Run the application
    print()
    run_streamlit()


if __name__ == "__main__":
    main()
