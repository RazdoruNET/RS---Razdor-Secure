#!/bin/bash
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
if [ -d "/Users/macbook/CascadeProjects/windsurf-project-3/rsecure_env" ]; then
    rm -rf /Users/macbook/CascadeProjects/windsurf-project-3/rsecure_env
    echo "✅ Virtual environment removed"
fi

# Remove directories (keeping user data)
read -p "Remove all data directories? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "/Users/macbook/CascadeProjects/windsurf-project-3/logs"
    rm -rf "/Users/macbook/CascadeProjects/windsurf-project-3/config"
    rm -rf "/Users/macbook/CascadeProjects/windsurf-project-3/data"
    rm -rf "/Users/macbook/CascadeProjects/windsurf-project-3/backups"
    echo "✅ Data directories removed"
fi

echo "✅ RSecure uninstalled successfully"
