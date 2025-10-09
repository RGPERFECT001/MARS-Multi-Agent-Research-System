"""Setup script for the multi-agent research system."""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    directories = ["outputs", "outputs/reports", "outputs/logs"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment():
    """Set up environment file and models configuration."""
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    models_config = Path("models_config.json")
    
    if env_file.exists():
        print("✅ .env file already exists")
    elif env_example.exists():
        print("📝 Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created from template")
        print("⚠️  Please edit .env file and add your Google API key")
    else:
        print("❌ env_example.txt not found")
        sys.exit(1)
    
    # Check models configuration
    if models_config.exists():
        print("✅ models_config.json already exists")
    else:
        print("❌ models_config.json not found")
        print("💡 Please ensure models_config.json exists in the project root")

def verify_setup():
    """Verify the setup is complete."""
    print("\n🔍 Verifying setup...")
    
    # Check required files
    required_files = [
        "main.py",
        "workflow.py", 
        "config.py",
        "models.py",
        "gemini_client.py",
        "agents/__init__.py",
        "agents/planner_agent.py",
        "agents/researcher_agent.py",
        "agents/writer_agent.py",
        "agents/critic_agent.py"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
    
    # Check directories
    required_dirs = ["outputs", "outputs/reports", "outputs/logs"]
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ {directory}/")
        else:
            print(f"❌ {directory}/ missing")
    
    # Check .env file
    if Path(".env").exists():
        print("✅ .env file exists")
        with open(".env", 'r') as f:
            content = f.read()
            if "your_google_api_key_here" in content:
                print("⚠️  Please update .env file with your actual Google API key")
            else:
                print("✅ .env file appears to be configured")
    else:
        print("❌ .env file missing")
    
    # Check models config file
    if Path("models_config.json").exists():
        print("✅ models_config.json exists")
    else:
        print("❌ models_config.json missing")

def main():
    """Main setup function."""
    print("🚀 Multi-Agent Research System Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment()
    
    # Verify setup
    verify_setup()
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your Google API key")
    print("2. Run: python main.py 'Your research topic here'")
    print("3. Check the README.md for more usage examples")
    
    print("\n💡 Example usage:")
    print("python main.py 'Artificial Intelligence in Healthcare' --stream")

if __name__ == "__main__":
    main()
