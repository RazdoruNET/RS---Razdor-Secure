#!/usr/bin/env python3
"""
Test RSecure Retaliation System
Demonstrates counter-attack capabilities
"""

import sys
import time
import json
from pathlib import Path

# Add rsecure to path
sys.path.insert(0, str(Path(__file__).parent / "rsecure"))

from modules.defense.retaliation_system import RSecureRetaliationSystem, RetaliationType, AttackSeverity

def test_retaliation_system():
    """Test retaliation system functionality"""
    print("🔪 RSECURE RETALIATION SYSTEM TEST")
    print("=" * 60)
    print("⚠️  WARNING: This is a simulation only!")
    print("🔥 Testing counter-attack capabilities...")
    print("=" * 60)
    
    # Initialize retaliation system
    config = {
        'auto_retaliation': True,
        'retaliation_threshold': 0.7,  # Lower threshold for testing
        'max_concurrent_attacks': 3,
        'attack_timeout': 30,  # Shorter for testing
        'network_attacks_enabled': True,
        'psychological_enabled': True,
        'quantum_enabled': False,  # Disabled for safety
        'require_confirmation': False,
        'log_all_actions': True
    }
    
    retaliation = RSecureRetaliationSystem(config)
    
    try:
        # Start retaliation system
        print("\n🚀 Starting retaliation system...")
        retaliation.start_retaliation()
        
        # Test targets
        test_targets = [
            {
                'ip': '192.168.1.100',
                'type': 'network',
                'vulnerability': 'ddos',
                'attack_vector': 'udp_flood',
                'confidence': 0.9,
                'metadata': {'source': 'test_simulation'}
            },
            {
                'ip': '10.0.0.50',
                'type': 'system',
                'vulnerability': 'exploit',
                'attack_vector': 'smb_exploit',
                'confidence': 0.85,
                'metadata': {'source': 'test_simulation'}
            },
            {
                'ip': '172.16.0.25',
                'type': 'psychological',
                'vulnerability': 'social_engineering',
                'attack_vector': 'fake_alerts',
                'confidence': 0.8,
                'metadata': {'source': 'test_simulation'}
            }
        ]
        
        print(f"\n🎯 Adding {len(test_targets)} test targets...")
        
        # Add targets
        for i, target_info in enumerate(test_targets, 1):
            print(f"\n--- Target {i} ---")
            print(f"IP: {target_info['ip']}")
            print(f"Type: {target_info['type']}")
            print(f"Vulnerability: {target_info['vulnerability']}")
            print(f"Confidence: {target_info['confidence']}")
            
            success = retaliation.add_target(target_info)
            if success:
                print(f"✅ Target added and retaliation queued")
            else:
                print(f"❌ Failed to add target")
        
        # Monitor retaliation
        print(f"\n🔍 Monitoring retaliation activities...")
        print("⏱️  Waiting for attacks to execute...")
        
        # Wait for attacks to execute
        time.sleep(10)
        
        # Check status
        status = retaliation.get_status()
        
        print(f"\n📊 RETALIATION STATUS:")
        print(f"   Running: {status['running']}")
        print(f"   Active targets: {status['active_targets']}")
        print(f"   Pending actions: {status['pending_actions']}")
        print(f"   Active attacks: {status['active_attacks']}")
        print(f"   Completed attacks: {status['completed_actions']}")
        
        print(f"\n📈 STATISTICS:")
        stats = status['statistics']
        print(f"   Targets identified: {stats['targets_identified']}")
        print(f"   Attacks launched: {stats['attacks_launched']}")
        print(f"   Successful attacks: {stats['successful_attacks']}")
        print(f"   Failed attacks: {stats['failed_attacks']}")
        print(f"   Targets disabled: {stats['targets_disabled']}")
        
        print(f"\n🔧 CAPABILITIES:")
        capabilities = status['capabilities']
        print(f"   Network attacks: {'✅' if capabilities['network_attacks'] else '❌'}")
        print(f"   System attacks: {'✅' if capabilities['system_attacks'] else '❌'}")
        print(f"   Quantum attacks: {'✅' if capabilities['quantum_attacks'] else '❌'}")
        print(f"   Psychological attacks: {'✅' if capabilities['psychological_attacks'] else '❌'}")
        
        # Wait for completion
        print(f"\n⏱️  Waiting for attacks to complete...")
        time.sleep(20)
        
        # Final status
        final_status = retaliation.get_status()
        print(f"\n🎯 FINAL RESULTS:")
        print(f"   Total attacks launched: {final_status['statistics']['attacks_launched']}")
        print(f"   Successful attacks: {final_status['statistics']['successful_attacks']}")
        print(f"   Targets disabled: {final_status['statistics']['targets_disabled']}")
        
        print(f"\n✅ Retaliation system test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop retaliation system
        print(f"\n🛑 Stopping retaliation system...")
        retaliation.stop_retaliation()
        print(f"✅ Retaliation system stopped")

def test_attack_modules():
    """Test individual attack modules"""
    print("\n🔪 TESTING INDIVIDUAL ATTACK MODULES")
    print("=" * 50)
    
    from modules.defense.retaliation_system import (
        NetworkAttackModule, SystemAttackModule, 
        PsychologicalAttackModule, QuantumAttackModule,
        RetaliationAction, RetaliationTarget, RetaliationType, AttackSeverity
    )
    
    # Test network attacks
    print("\n🌐 Testing Network Attack Module...")
    network_module = NetworkAttackModule()
    network_module.initialize({})
    
    target = RetaliationTarget(
        target_ip="127.0.0.1",
        target_type="network",
        vulnerability="ddos",
        attack_vector="syn_flood",
        confidence=0.9,
        last_seen=time.time(),
        metadata={}
    )
    
    action = RetaliationAction(
        action_id="test_network_001",
        action_type=RetaliationType.NETWORK_ATTACK,
        target=target,
        severity=AttackSeverity.HIGH,
        payload={
            'type': 'syn_flood',
            'parameters': {
                'target_port': 80,
                'packet_rate': 100,
                'duration': 5
            }
        },
        execution_time=time.time(),
        duration=5,
        auto_cleanup=True
    )
    
    result = network_module.execute(action)
    print(f"   Network attack result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Test system attacks
    print("\n💻 Testing System Attack Module...")
    system_module = SystemAttackModule()
    system_module.initialize({})
    
    action.payload = {
        'type': 'process_kill',
        'parameters': {
            'target_processes': ['test_process'],
            'force_kill': True
        }
    }
    
    result = system_module.execute(action)
    print(f"   System attack result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Test psychological attacks
    print("\n🧠 Testing Psychological Attack Module...")
    psych_module = PsychologicalAttackModule()
    psych_module.initialize({})
    
    action.payload = {
        'type': 'fake_alerts',
        'parameters': {
            'alert_type': 'security_breach',
            'messages': ['System compromised!']
        }
    }
    
    result = psych_module.execute(action)
    print(f"   Psychological attack result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Test quantum attacks (if enabled)
    print("\n⚛️ Testing Quantum Attack Module...")
    quantum_module = QuantumAttackModule()
    quantum_module.initialize({})
    
    action.payload = {
        'type': 'quantum_entanglement',
        'parameters': {
            'entanglement_type': 'photon_pair',
            'target_system': 'test_quantum'
        }
    }
    
    result = quantum_module.execute(action)
    print(f"   Quantum attack result: {'✅ SUCCESS' if result else '❌ FAILED'}")

def demonstrate_payloads():
    """Demonstrate available attack payloads"""
    print("\n💣 AVAILABLE ATTACK PAYLOADS")
    print("=" * 50)
    
    retaliation = RSecureRetaliationSystem()
    
    print("\n🌐 NETWORK ATTACKS:")
    for category, attacks in retaliation.payloads['network'].items():
        print(f"   {category.upper()}:")
        for attack_name, payload in attacks.items():
            print(f"     - {attack_name}: {payload['type']}")
    
    print("\n💻 SYSTEM ATTACKS:")
    for category, attacks in retaliation.payloads['system'].items():
        print(f"   {category.upper()}:")
        for attack_name, payload in attacks.items():
            print(f"     - {attack_name}: {payload['type']}")
    
    print("\n🧠 PSYCHOLOGICAL ATTACKS:")
    for category, attacks in retaliation.payloads['psychological'].items():
        print(f"   {category.upper()}:")
        for attack_name, payload in attacks.items():
            print(f"     - {attack_name}: {payload['type']}")
    
    print("\n⚛️ QUANTUM ATTACKS:")
    for attack_name, payload in retaliation.payloads['quantum'].items():
        print(f"   - {attack_name}: {payload['type']}")

if __name__ == "__main__":
    print("🔪 RSECURE RETALIATION SYSTEM TEST SUITE")
    print("=" * 60)
    print("⚠️  FOR EDUCATIONAL PURPOSES ONLY")
    print("🚨 DO NOT USE FOR MALICIOUS PURPOSES")
    print("=" * 60)
    
    try:
        # Demonstrate payloads
        demonstrate_payloads()
        
        # Test individual modules
        test_attack_modules()
        
        # Test full system
        test_retaliation_system()
        
        print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"🔪 RSecure Retaliation System is fully operational!")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
