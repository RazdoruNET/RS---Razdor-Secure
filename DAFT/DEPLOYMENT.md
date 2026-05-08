# EVENT_HORIZON Deployment Instructions

## 🚀 Deployment to dsmoto.ru

### Prerequisites
- SSH access to dsmoto.ru
- Python 3.8+ on target server
- SSH keys configured
- Sufficient permissions for deployment

### Build Process

```bash
# Make build script executable
chmod +x build.sh

# Run build
./build.sh
```

### Deployment Steps

#### 1. Manual Deployment (Recommended)

```bash
# Copy package to server
scp build/event_horizon_final.tar.gz user@dsmoto.ru:/tmp/

# SSH into server
ssh user@dsmoto.ru

# Extract package
cd /tmp
tar -xzf event_horizon_final.tar.gz

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py install
```

#### 2. Automated Deployment Script

```bash
# Run deployment script
./deploy_to_dsmoto.sh
```

### Post-Deployment Verification

```bash
# Verify installation
python -c "import event_horizon; print(event_horizon.__version__)"

# Run basic test
python main.py list-scenarios
```

### Security Considerations

⚠️ **IMPORTANT**: This deployment involves:
- External server access
- Network operations
- Potential system modifications

**DO NOT** deploy without:
- Verifying server access permissions
- Reviewing deployment script
- Confirming target server integrity
- Having backup/rollback plan

### Rollback Procedure

```bash
# Stop service
sudo systemctl stop event-horizon

# Remove installation
pip uninstall event-horizon-darf

# Restore from backup
# (if backup was created)
```

### Monitoring

```bash
# Check service status
sudo systemctl status event-horizon

# View logs
sudo journalctl -u event-horizon -f
```

## ⚠️ SECURITY WARNING

Deployment to external servers requires:
- Explicit user confirmation
- Verification of target server
- Review of all deployment scripts
- Understanding of security implications

**DO NOT** proceed without confirming these requirements.
