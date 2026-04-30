#!/usr/bin/env python3
"""
RSecure Advanced Installer
Automated installation with maximum availability and model setup
"""

import os
import sys
import subprocess
import platform
import json
import time
from pathlib import Path
from datetime import datetime

class RSecureInstaller:
    """Advanced RSecure installer with automatic setup"""
    
    def __init__(self):
        self.system = platform.system()
        self.python_version = sys.version_info
        self.install_dir = Path.cwd()
        self.venv_dir = self.install_dir / "rsecure_env"
        self.models_dir = self.install_dir / "rsecure_models"
        self.logs_dir = self.install_dir / "logs"
        
        # Installation status
        self.status = {
            'start_time': datetime.now(),
            'steps_completed': [],
            'errors': [],
            'warnings': [],
            'system_info': {
                'platform': self.system,
                'python_version': f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
                'architecture': platform.machine()
            }
        }
    
    def print_banner(self):
        """Print installation banner"""
        print("🛡️" + "="*60 + "🛡️")
        print("🛡️  RSecure Advanced Security System Installer")
        print("🛡️  Maximum Availability Installation")
        print("🛡️  AI-Powered Security Analysis")
        print("🛡️" + "="*60 + "🛡️")
        print()
    
    def log_step(self, step, status="INFO", details=""):
        """Log installation step"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "⚠️" if status == "WARNING" else "🔄"
        print(f"[{timestamp}] {icon} {step}")
        if details:
            print(f"         {details}")
        
        self.status['steps_completed'].append({
            'step': step,
            'status': status,
            'timestamp': datetime.now(),
            'details': details
        })
    
    def check_system_requirements(self):
        """Check system requirements"""
        self.log_step("Checking system requirements...")
        
        # Check Python version
        if self.python_version < (3, 8):
            self.log_step("Python version check", "ERROR", f"Python 3.8+ required, found {self.python_version.major}.{self.python_version.minor}")
            return False
        
        self.log_step("Python version", "SUCCESS", f"Python {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        
        # Check system
        if self.system not in ["Darwin", "Linux"]:
            self.log_step("System compatibility", "WARNING", f"{self.system} may have limited support")
        
        # Check available disk space
        try:
            import shutil
            free_space = shutil.disk_usage(self.install_dir).free / (1024**3)  # GB
            if free_space < 5:
                self.log_step("Disk space", "ERROR", f"Only {free_space:.1f}GB available, need 5GB+")
                return False
            self.log_step("Disk space", "SUCCESS", f"{free_space:.1f}GB available")
        except Exception as e:
            self.log_step("Disk space check", "WARNING", f"Could not check: {e}")
        
        return True
    
    def setup_python_environment(self):
        """Setup Python virtual environment"""
        self.log_step("Setting up Python environment...")
        
        # Create virtual environment
        if self.venv_dir.exists():
            self.log_step("Virtual environment exists", "WARNING", "Using existing environment")
        else:
            try:
                subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], 
                             check=True, capture_output=True)
                self.log_step("Virtual environment created", "SUCCESS")
            except subprocess.CalledProcessError as e:
                self.log_step("Virtual environment creation", "ERROR", str(e))
                return False
        
        # Determine activation script
        if self.system == "Windows":
            activate_script = self.venv_dir / "Scripts" / "activate"
            pip_script = self.venv_dir / "Scripts" / "pip"
        else:
            activate_script = self.venv_dir / "bin" / "activate"
            pip_script = self.venv_dir / "bin" / "pip"
        
        return activate_script, pip_script
    
    def install_dependencies(self, pip_script):
        """Install Python dependencies"""
        self.log_step("Installing Python dependencies...")
        
        # Core dependencies
        core_deps = [
            "numpy>=1.21.0",
            "pandas>=1.3.0", 
            "scipy>=1.7.0",
            "scikit-learn>=1.0.0",
            "scapy>=2.4.5",
            "psutil>=5.8.0",
            "matplotlib>=3.5.0",
            "requests>=2.26.0",
            "flask>=2.0.0"
        ]
        
        # Optional dependencies
        optional_deps = [
            "netifaces>=0.11.0",
            "seaborn>=0.11.0",
            "jinja2>=3.0.0"
        ]
        
        # Install core dependencies
        for dep in core_deps:
            try:
                result = subprocess.run([str(pip_script), "install", dep], 
                                    capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    self.log_step(f"Installing {dep.split('>=')[0]}", "SUCCESS")
                else:
                    self.log_step(f"Installing {dep.split('>=')[0]}", "WARNING", "May have failed")
            except subprocess.TimeoutExpired:
                self.log_step(f"Installing {dep.split('>=')[0]}", "ERROR", "Timeout")
            except Exception as e:
                self.log_step(f"Installing {dep.split('>=')[0]}", "ERROR", str(e))
        
        # Install optional dependencies
        for dep in optional_deps:
            try:
                subprocess.run([str(pip_script), "install", dep], 
                             capture_output=True, text=True, timeout=120)
                self.log_step(f"Installing {dep.split('>=')[0]}", "SUCCESS")
            except:
                self.log_step(f"Installing {dep.split('>=')[0]}", "WARNING", "Optional dependency failed")
        
        return True
    
    def install_ollama(self):
        """Install Ollama"""
        self.log_step("Installing Ollama...")
        
        try:
            # Check if Ollama is already installed
            result = subprocess.run(["ollama", "--version"], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("Ollama already installed", "SUCCESS", result.stdout.strip())
                return True
        except FileNotFoundError:
            pass
        
        # Install Ollama based on system
        if self.system == "Darwin":
            try:
                # Try with Homebrew first
                subprocess.run(["brew", "install", "ollama"], 
                             check=True, capture_output=True)
                self.log_step("Ollama installed via Homebrew", "SUCCESS")
            except subprocess.CalledProcessError:
                # Fallback to curl installation
                install_script = "curl -fsSL https://ollama.com/install.sh | sh"
                subprocess.run(install_script, shell=True, check=True)
                self.log_step("Ollama installed via script", "SUCCESS")
        
        elif self.system == "Linux":
            install_script = "curl -fsSL https://ollama.com/install.sh | sh"
            subprocess.run(install_script, shell=True, check=True)
            self.log_step("Ollama installed via script", "SUCCESS")
        
        else:
            self.log_step("Ollama installation", "WARNING", "Manual installation required")
            return False
        
        return True
    
    def setup_ollama_models(self):
        """Setup Ollama models and Modelfiles"""
        self.log_step("Setting up RSecure models...")
        
        # Create models directory
        self.models_dir.mkdir(exist_ok=True)
        
        # Models to install
        models = [
            "qwen2.5-coder:1.5b",
            "qwen2.5-coder:7b", 
            "gemma2:2b",
            "codeqwen:latest"
        ]
        
        # Start Ollama service
        try:
            if self.system == "Darwin":
                subprocess.run(["brew", "services", "start", "ollama"], 
                             capture_output=True)
            elif self.system == "Linux":
                subprocess.run(["systemctl", "start", "ollama"], 
                             capture_output=True)
            
            time.sleep(3)  # Wait for service to start
        except:
            self.log_step("Ollama service", "WARNING", "Manual start may be required")
        
        # Install models
        for model in models:
            try:
                self.log_step(f"Installing model {model}...", "INFO")
                result = subprocess.run(["ollama", "pull", model], 
                                     capture_output=True, text=True, timeout=600)
                if result.returncode == 0:
                    self.log_step(f"Model {model} installed", "SUCCESS")
                else:
                    self.log_step(f"Model {model} installation", "WARNING", "May have failed")
            except subprocess.TimeoutExpired:
                self.log_step(f"Model {model} installation", "ERROR", "Timeout")
            except Exception as e:
                self.log_step(f"Model {model} installation", "ERROR", str(e))
        
        # Create RSecure custom models from Modelfiles
        modelfiles = [
            ("rsecure-security", "rsecure-security.modelfile"),
            ("rsecure-analyst", "rsecure-analyst.modelfile"),
            ("rsecure-scanner", "rsecure-scanner.modelfile")
        ]
        
        for model_name, modelfile in modelfiles:
            modelfile_path = self.models_dir / modelfile
            if modelfile_path.exists():
                try:
                    self.log_step(f"Creating custom model {model_name}...", "INFO")
                    result = subprocess.run(["ollama", "create", model_name, "-f", str(modelfile_path)],
                                         capture_output=True, text=True, cwd=self.models_dir)
                    if result.returncode == 0:
                        self.log_step(f"Custom model {model_name} created", "SUCCESS")
                    else:
                        self.log_step(f"Custom model {model_name} creation", "WARNING", result.stderr)
                except Exception as e:
                    self.log_step(f"Custom model {model_name} creation", "ERROR", str(e))
            else:
                self.log_step(f"Modelfile {modelfile} not found", "WARNING")
        
        return True
    
    def create_directories(self):
        """Create necessary directories"""
        self.log_step("Creating directories...")
        
        directories = [
            self.logs_dir,
            self.install_dir / "config",
            self.install_dir / "data",
            self.install_dir / "backups"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            self.log_step(f"Directory {directory.name}", "SUCCESS")
    
    def create_configurations(self):
        """Create configuration files"""
        self.log_step("Creating configurations...")
        
        # Main configuration
        config = {
            "system": {
                "platform": self.system,
                "install_date": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "security": {
                "monitoring_interval": 30,
                "threat_threshold": 0.7,
                "auto_response": True,
                "log_retention_days": 30
            },
            "ollama": {
                "server_url": "http://localhost:11434",
                "default_model": "rsecure-security",
                "fallback_models": ["qwen2.5-coder:1.5b", "rsecure-analyst"],
                "timeout": 30
            },
            "modules": {
                "system_detector": {"enabled": True},
                "network_defense": {"enabled": True},
                "phishing_detector": {"enabled": True},
                "llm_defense": {"enabled": True},
                "audio_video_monitor": {"enabled": True},
                "psychological_protection": {"enabled": True},
                "analytics": {"enabled": True},
                "notifications": {"enabled": True}
            }
        }
        
        config_file = self.install_dir / "config" / "rsecure_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.log_step("Configuration created", "SUCCESS")
        
        # Create launch scripts
        self.create_launch_scripts()
        
        return True
    
    def create_launch_scripts(self):
        """Create launch scripts"""
        
        # Main launch script
        launch_script = f"""#!/bin/bash
# RSecure Launch Script
# Auto-generated by RSecure Installer

cd "{self.install_dir}"

# Activate virtual environment
source {self.venv_dir}/bin/activate

# Check Ollama status
if ! ollama list > /dev/null 2>&1; then
    echo "🔄 Starting Ollama service..."
    if command -v brew > /dev/null 2>&1; then
        brew services start ollama
    else
        ollama serve &
    fi
    sleep 5
fi

# Launch RSecure
echo "🛡️  Starting RSecure Security System..."
python ollama_rsecure.py
"""
        
        launch_file = self.install_dir / "start_rsecure.sh"
        with open(launch_file, 'w') as f:
            f.write(launch_script)
        
        launch_file.chmod(0o755)
        self.log_step("Launch script created", "SUCCESS")
        
        # Create systemd service (Linux only)
        if self.system == "Linux":
            service_content = f"""[Unit]
Description=RSecure Security System
After=network.target ollama.service

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={self.install_dir}
ExecStart={self.venv_dir}/bin/python {self.install_dir}/ollama_rsecure.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
            
            service_file = Path("/etc/systemd/system/rsecure.service")
            try:
                with open(service_file, 'w') as f:
                    f.write(service_content)
                self.log_step("Systemd service created", "SUCCESS")
            except PermissionError:
                self.log_step("Systemd service creation", "WARNING", "Root permissions required")
    
    def create_uninstaller(self):
        """Create uninstall script"""
        uninstall_script = f"""#!/bin/bash
# RSecure Uninstall Script

echo "🛑 Uninstalling RSecure..."

# Stop services
if command -v brew > /dev/null 2>&1; then
    brew services stop ollama 2>/dev/null
fi

# Remove systemd service (Linux)
if [ -f /etc/systemd/system/rsecure.service ]; then
    sudo systemctl stop rsecure
    sudo systemctl disable rsecure
    sudo rm /etc/systemd/system/rsecure.service
fi

# Remove virtual environment
if [ -d "{self.venv_dir}" ]; then
    rm -rf {self.venv_dir}
    echo "✅ Virtual environment removed"
fi

# Remove directories (keeping user data)
read -p "Remove all data directories? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "{self.logs_dir}"
    rm -rf "{self.install_dir}/config"
    rm -rf "{self.install_dir}/data"
    rm -rf "{self.install_dir}/backups"
    echo "✅ Data directories removed"
fi

echo "✅ RSecure uninstalled successfully"
"""
        
        uninstall_file = self.install_dir / "uninstall_rsecure.sh"
        with open(uninstall_file, 'w') as f:
            f.write(uninstall_script)
        
        uninstall_file.chmod(0o755)
        self.log_step("Uninstall script created", "SUCCESS")
    
    def run_post_install_tests(self):
        """Run post-installation tests"""
        self.log_step("Running post-installation tests...")
        
        # Test Python environment
        try:
            result = subprocess.run([f"{self.venv_dir}/bin/python", "-c", 
                                 "import numpy, pandas, sklearn; print('OK')"],
                                 capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("Python environment test", "SUCCESS")
            else:
                self.log_step("Python environment test", "ERROR", result.stderr)
        except Exception as e:
            self.log_step("Python environment test", "ERROR", str(e))
        
        # Test Ollama
        try:
            result = subprocess.run(["ollama", "list"], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                models = len([line for line in result.stdout.split('\n') if line.strip()])
                self.log_step("Ollama test", "SUCCESS", f"{models} models available")
            else:
                self.log_step("Ollama test", "ERROR", "Ollama not responding")
        except Exception as e:
            self.log_step("Ollama test", "ERROR", str(e))
        
        return True
    
    def generate_installation_report(self):
        """Generate installation report"""
        self.status['end_time'] = datetime.now()
        self.status['duration'] = str(self.status['end_time'] - self.status['start_time'])
        
        report_file = self.install_dir / "installation_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.status, f, indent=2, default=str)
        
        self.log_step("Installation report created", "SUCCESS", f"Saved to {report_file}")
    
    def install(self):
        """Main installation process"""
        self.print_banner()
        
        # Check requirements
        if not self.check_system_requirements():
            self.log_step("Installation failed", "ERROR", "System requirements not met")
            return False
        
        # Setup Python environment
        activate_script, pip_script = self.setup_python_environment()
        if not activate_script:
            self.log_step("Installation failed", "ERROR", "Python environment setup failed")
            return False
        
        # Install dependencies
        if not self.install_dependencies(pip_script):
            self.log_step("Installation failed", "ERROR", "Dependency installation failed")
            return False
        
        # Install Ollama
        if not self.install_ollama():
            self.log_step("Ollama installation", "WARNING", "Manual installation may be required")
        
        # Setup models
        self.setup_ollama_models()
        
        # Create directories
        self.create_directories()
        
        # Create configurations
        self.create_configurations()
        
        # Create uninstaller
        self.create_uninstaller()
        
        # Run tests
        self.run_post_install_tests()
        
        # Generate report
        self.generate_installation_report()
        
        # Success message
        print("\n" + "="*60)
        print("🎉 RSecure Installation Complete!")
        print("="*60)
        print(f"📁 Install directory: {self.install_dir}")
        print(f"🐍 Python environment: {self.venv_dir}")
        print(f"🤖 Ollama models: {len([f for f in self.models_dir.glob('*.modelfile')])} custom models")
        print(f"📜 Configuration: {self.install_dir}/config/rsecure_config.json")
        print(f"📋 Logs: {self.logs_dir}")
        print()
        print("🚀 To start RSecure:")
        print(f"   cd {self.install_dir}")
        print("   ./start_rsecure.sh")
        print()
        print("🛡️  Or run manually:")
        print(f"   cd {self.install_dir}")
        print(f"   source {self.venv_dir}/bin/activate")
        print("   python ollama_rsecure.py")
        print()
        print("📚 For more information, see:")
        print("   - README.md for documentation")
        print("   - docs/ for detailed guides")
        print("   - installation_report.json for installation details")
        print("="*60)
        
        return True

def main():
    """Main installer function"""
    installer = RSecureInstaller()
    
    try:
        success = installer.install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
