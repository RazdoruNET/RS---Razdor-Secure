# Authorization Documents Setup

## 🚨 CRITICAL: Authorization Required

EVENT_HORIZON requires formal authorization before conducting any security audit against external targets.

## 📋 Required Documents

Place the following documents in this directory:

### 1. authorization_letter.pdf
- Written authorization on company letterhead
- Signed by authorized representative
- Includes authorization reference number
- Specifies authorized testing scope

### 2. scope_of_engagement.pdf
- Detailed scope of engagement document
- Authorized test types
- Time windows for testing
- Contact information
- Emergency procedures

### 3. authorized_targets.txt
List of authorized targets, one per line:
```
https://dsmoto.ru
https://api.dsmoto.ru
```

### 4. contact_info.txt
Contact information for coordination:
```
Security Team: security@dsmoto.ru
Phone: +1-555-0123
Emergency: +1-555-9999
```

### 5. authorization.json
Copy and fill in the template:
```bash
cp authorization_template.json authorization.json
# Edit authorization.json with your details
```

## 🔐 Authorization Process

### Step 1: Prepare Documents
1. Obtain written authorization from target organization
2. Complete scope of engagement document
3. Fill in authorization.json with correct details
4. Place all documents in this directory

### Step 2: Validate Authorization
```bash
python -m src.authorized_audit --validate --target https://dsmoto.ru
```

### Step 3: Run Authorized Audit
```bash
python -m src.authorized_audit --target https://dsmoto.ru
```

## ⚠️ Important Notes

- **Authorization is mandatory** - no external testing without it
- **Time windows must be respected** - testing outside authorized window is prohibited
- **Resource limits are enforced** - exceeding limits will stop the audit
- **Contact verification required** - authorization may be verified with authorized contact
- **Emergency procedures** - if issues occur, contact immediately

## 🚫 What Happens Without Authorization

If authorization documents are missing or invalid:
- Audit will NOT proceed
- Error message will explain what's missing
- System will remain in isolated lab mode only

## 📞 Questions?

Contact the EVENT_HORIZON security team for authorization assistance.
