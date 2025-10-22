#!/usr/bin/env python3
"""
Startup script to run both the API server and frontend server.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_requirements():
    """Check if required dependencies are installed."""
    try:
        import flask
        import flask_cors
        print("✅ Flask dependencies found")
        return True
    except ImportError:
        print("❌ Missing Flask dependencies. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-api.txt"])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False

def check_config():
    """Check if configuration files exist."""
    config_path = Path("ai_crm_automation/config.json")
    env_path = Path(".env")
    
    if config_path.exists():
        print("✅ Configuration file found")
        return True
    elif env_path.exists():
        print("✅ Environment file found")
        return True
    else:
        print("⚠️  No configuration found. Make sure to set up your API keys.")
        print("   Create ai_crm_automation/config.json or .env file with your credentials.")
        return False

def start_servers():
    """Start both API and frontend servers."""
    print("🚀 Starting AI CRM servers...")
    
    # Start API server
    print("📡 Starting API server on port 8000...")
    api_process = subprocess.Popen([
        sys.executable, "api_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait a moment for API server to start
    time.sleep(2)
    
    # Start frontend server
    print("🌐 Starting frontend server on port 3000...")
    frontend_process = subprocess.Popen([
        sys.executable, "serve_frontend.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait a moment for frontend server to start
    time.sleep(2)
    
    print("\n" + "="*50)
    print("🎉 AI CRM is now running!")
    print("🌐 Frontend: http://localhost:3000")
    print("📡 API: http://localhost:8000")
    print("📚 Health check: http://localhost:8000/health")
    print("⏹️  Press Ctrl+C to stop both servers")
    print("="*50 + "\n")
    
    # Open browser
    webbrowser.open('http://localhost:3000')
    
    try:
        # Wait for both processes
        api_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        api_process.terminate()
        frontend_process.terminate()
        
        # Wait for processes to terminate
        api_process.wait()
        frontend_process.wait()
        
        print("👋 Servers stopped successfully")

def main():
    print("🤖 AI CRM Startup Script")
    print("=" * 30)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        print("\n⚠️  Continuing without configuration check...")
        print("   Make sure to configure your API keys before using the system.")
    
    # Start servers
    try:
        start_servers()
    except Exception as e:
        print(f"❌ Error starting servers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()