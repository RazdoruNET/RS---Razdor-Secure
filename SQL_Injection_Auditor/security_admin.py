#!/usr/bin/env python3
"""
Security Administration Tool
Manage authorization tokens and security policies
"""

import json
import hashlib
import getpass
from datetime import datetime, timezone, timedelta
from modules.security import SecurityManager, SecurityLevel

class SecurityAdmin:
    """Security administration interface"""
    
    def __init__(self):
        self.security_manager = SecurityManager()
    
    def create_authorization_token(self):
        """Create new authorization token"""
        print("\n=== Create Authorization Token ===")
        
        # Get scope
        print("Enter allowed targets (one per line, empty line to finish):")
        scope = []
        while True:
            target = input("Target: ").strip()
            if not target:
                break
            if target.startswith(('http://', 'https://')):
                scope.append(target)
            else:
                print("Invalid target format. Use http:// or https://")
        
        if not scope:
            print("No targets specified. Using read-only mode.")
            security_level = SecurityLevel.READ_ONLY
            capabilities = ['generate_payloads', 'analyze_responses']
        else:
            # Get security level
            print("\nSecurity Levels:")
            print("1. READ_ONLY - Generate payloads only")
            print("2. ANALYSIS - Analyze responses")
            print("3. ACTIVE_TESTING - Execute requests")
            print("4. FULL_AUDIT - All capabilities")
            
            level_choice = input("Select level (1-4): ").strip()
            level_map = {
                '1': SecurityLevel.READ_ONLY,
                '2': SecurityLevel.ANALYSIS,
                '3': SecurityLevel.ACTIVE_TESTING,
                '4': SecurityLevel.FULL_AUDIT
            }
            
            security_level = level_map.get(level_choice, SecurityLevel.READ_ONLY)
            
            # Set capabilities based on level
            if security_level == SecurityLevel.READ_ONLY:
                capabilities = ['generate_payloads', 'analyze_responses']
            elif security_level == SecurityLevel.ANALYSIS:
                capabilities = ['generate_payloads', 'analyze_responses', 'export_reports']
            elif security_level == SecurityLevel.ACTIVE_TESTING:
                capabilities = ['generate_payloads', 'analyze_responses', 'export_reports', 'execute_requests']
            else:  # FULL_AUDIT
                capabilities = ['generate_payloads', 'analyze_responses', 'export_reports', 'execute_requests', 'bypass_waf', 'modify_config']
        
        # Get expiration
        hours = input("Token expires in hours (default 24): ").strip()
        expires_hours = int(hours) if hours.isdigit() else 24
        
        # Get purpose
        purpose = input("Purpose of this token: ").strip() or "Security audit"
        
        # Create token
        token = self.security_manager.generate_auth_token(
            scope=scope,
            security_level=security_level,
            capabilities=capabilities,
            expires_hours=expires_hours,
            created_by=getpass.getuser(),
            purpose=purpose
        )
        
        print(f"\n✅ Authorization Token Created:")
        print(f"Token: {token}")
        print(f"Scope: {scope}")
        print(f"Security Level: {security_level.value}")
        print(f"Capabilities: {capabilities}")
        print(f"Expires: {datetime.now(timezone.utc) + timedelta(hours=expires_hours)}")
        print(f"Purpose: {purpose}")
        
        # Save to file
        filename = f"auth_token_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'token': token,
                'scope': scope,
                'security_level': security_level.value,
                'capabilities': capabilities,
                'expires_at': (datetime.now(timezone.utc) + timedelta(hours=expires_hours)).isoformat(),
                'purpose': purpose
            }, f, indent=2)
        
        print(f"Token saved to: {filename}")
    
    def configure_security(self):
        """Configure security settings"""
        print("\n=== Security Configuration ===")
        
        # Load current config
        try:
            with open('security_config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {
                "allowed_targets": [],
                "blocked_domains": ["localhost", "127.0.0.1", "internal"],
                "max_security_level": "analysis",
                "require_auth": True
            }
        
        print("Current configuration:")
        print(json.dumps(config, indent=2))
        
        print("\nConfiguration Options:")
        print("1. Add allowed target")
        print("2. Remove allowed target")
        print("3. Add blocked domain")
        print("4. Remove blocked domain")
        print("5. Set max security level")
        print("6. Toggle authentication requirement")
        print("7. Save and exit")
        
        while True:
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == '1':
                target = input("Enter target to allow: ").strip()
                if target.startswith(('http://', 'https://')):
                    config['allowed_targets'].append(target)
                    print(f"Added {target} to allowed targets")
                else:
                    print("Invalid target format")
            
            elif choice == '2':
                target = input("Enter target to remove: ").strip()
                if target in config['allowed_targets']:
                    config['allowed_targets'].remove(target)
                    print(f"Removed {target} from allowed targets")
                else:
                    print("Target not found")
            
            elif choice == '3':
                domain = input("Enter domain to block: ").strip()
                config['blocked_domains'].append(domain)
                print(f"Added {domain} to blocked domains")
            
            elif choice == '4':
                domain = input("Enter domain to unblock: ").strip()
                if domain in config['blocked_domains']:
                    config['blocked_domains'].remove(domain)
                    print(f"Removed {domain} from blocked domains")
                else:
                    print("Domain not found")
            
            elif choice == '5':
                print("Security levels: read_only, analysis, active_testing, full_audit")
                level = input("Enter max security level: ").strip()
                if level in ['read_only', 'analysis', 'active_testing', 'full_audit']:
                    config['max_security_level'] = level
                    print(f"Set max security level to {level}")
                else:
                    print("Invalid security level")
            
            elif choice == '6':
                current = config.get('require_auth', True)
                config['require_auth'] = not current
                print(f"Authentication requirement: {'ENABLED' if not current else 'DISABLED'}")
            
            elif choice == '7':
                with open('security_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                print("Security configuration saved")
                break
            
            else:
                print("Invalid choice")
    
    def view_audit_log(self):
        """View audit log"""
        print("\n=== Audit Log ===")
        
        try:
            import sqlite3
            conn = sqlite3.connect('audit.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, event_type, target, action, risk_score
                FROM audit_events 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''')
            
            events = cursor.fetchall()
            
            if not events:
                print("No audit events found")
                return
            
            print(f"{'Timestamp':<20} {'Event Type':<20} {'Target':<30} {'Action':<20} {'Risk':<5}")
            print("-" * 95)
            
            for event in events:
                timestamp, event_type, target, action, risk_score = event
                print(f"{timestamp:<20} {event_type:<20} {target[:30]:<30} {action:<20} {risk_score:<5}")
            
            conn.close()
            
        except Exception as e:
            print(f"Error reading audit log: {e}")
    
    def main_menu(self):
        """Main administration menu"""
        print("🔐 SQL Injection Auditor - Security Administration")
        
        while True:
            print("\nMain Menu:")
            print("1. Create Authorization Token")
            print("2. Configure Security Settings")
            print("3. View Audit Log")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == '1':
                self.create_authorization_token()
            elif choice == '2':
                self.configure_security()
            elif choice == '3':
                self.view_audit_log()
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Invalid choice")

if __name__ == '__main__':
    admin = SecurityAdmin()
    admin.main_menu()
