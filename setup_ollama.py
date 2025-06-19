#!/usr/bin/env python3
"""
Setup script for Ollama AI integration
This script helps users set up Ollama for AI-powered project planning
"""

import subprocess
import sys
import requests
import time
import platform

def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_ollama():
    """Install Ollama based on the operating system"""
    system = platform.system().lower()
    
    print("🤖 Installing Ollama...")
    
    if system == "linux" or system == "darwin":  # Linux or macOS
        try:
            # Download and run the install script
            subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh'], check=True)
            print("✅ Ollama installation script downloaded")
            subprocess.run(['sh', '-c', 'curl -fsSL https://ollama.ai/install.sh | sh'], check=True)
            print("✅ Ollama installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Ollama: {e}")
            print("Please visit https://ollama.ai for manual installation instructions")
            return False
    
    elif system == "windows":
        print("🪟 For Windows, please:")
        print("1. Visit https://ollama.ai")
        print("2. Download the Windows installer")
        print("3. Run the installer")
        print("4. Restart this script after installation")
        return False
    
    else:
        print(f"❌ Unsupported operating system: {system}")
        print("Please visit https://ollama.ai for installation instructions")
        return False
    
    return True

def check_ollama_running():
    """Check if Ollama service is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama service"""
    print("🚀 Starting Ollama service...")
    try:
        # Start Ollama in the background
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for service to start
        for i in range(30):  # Wait up to 30 seconds
            if check_ollama_running():
                print("✅ Ollama service started successfully")
                return True
            time.sleep(1)
            print(f"⏳ Waiting for Ollama to start... ({i+1}/30)")
        
        print("❌ Ollama service failed to start within 30 seconds")
        return False
        
    except Exception as e:
        print(f"❌ Failed to start Ollama: {e}")
        return False

def pull_model(model_name="llama3.2"):
    """Pull the specified model"""
    print(f"📥 Pulling {model_name} model...")
    print("⚠️  This may take several minutes depending on your internet connection")
    
    try:
        result = subprocess.run(['ollama', 'pull', model_name], check=True)
        print(f"✅ {model_name} model downloaded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to pull {model_name} model: {e}")
        return False

def test_ai_integration():
    """Test the AI integration"""
    print("🧪 Testing AI integration...")
    
    try:
        from ai import ollama_ai
        
        if not ollama_ai.is_available():
            print("❌ Ollama is not available")
            return False
        
        # Test a simple prompt
        response = ollama_ai.generate_response("Say 'Hello from Ollama!' in exactly those words.")
        
        if response and "Hello from Ollama!" in response:
            print("✅ AI integration test passed")
            print(f"🤖 AI Response: {response}")
            return True
        else:
            print("⚠️  AI integration test partially successful")
            print(f"🤖 AI Response: {response}")
            return True
            
    except Exception as e:
        print(f"❌ AI integration test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Ollama AI Integration for Project Manager")
    print("=" * 60)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("❌ Ollama is not installed")
        if not install_ollama():
            print("❌ Setup failed. Please install Ollama manually and run this script again.")
            return False
    else:
        print("✅ Ollama is already installed")
    
    # Check if Ollama is running
    if not check_ollama_running():
        print("❌ Ollama service is not running")
        if not start_ollama():
            print("❌ Failed to start Ollama service")
            print("💡 Try running 'ollama serve' manually in another terminal")
            return False
    else:
        print("✅ Ollama service is running")
    
    # Pull the model
    if not pull_model():
        print("❌ Failed to download AI model")
        return False
    
    # Test integration
    if not test_ai_integration():
        print("❌ AI integration test failed")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 What you can do now:")
    print("• Create AI-powered project plans")
    print("• Get intelligent project analysis")
    print("• Auto-adjust schedules based on progress")
    print("• Break down complex tasks into subtasks")
    print("\n🚀 Start your project manager and try the AI features!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
