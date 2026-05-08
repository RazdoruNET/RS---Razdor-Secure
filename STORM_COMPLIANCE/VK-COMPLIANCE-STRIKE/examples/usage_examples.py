#!/usr/bin/env python3
"""
VK-COMPLIANCE-STRIKE Usage Examples
Demonstrates various usage patterns and configurations
"""

import json
import time
from datetime import datetime
from pathlib import Path

# Import modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from main import VKComplianceStrike
from modules.legal_mining_vk import LegalMiningVK
from modules.vk_report_automation import VKReportAutomation
from modules.support_pressure import SupportPressure

def example_1_basic_scan():
    """Example 1: Basic content scanning"""
    print("=== Example 1: Basic Content Scanning ===")
    
    # Initialize with default config
    miner = LegalMiningVK()
    
    # Scan last 50 posts
    violations = miner.scan_group_wall(count=50)
    
    print(f"Scanned 50 posts, found {len(violations)} violations")
    
    # Display first few violations
    for i, violation in enumerate(violations[:3]):
        print(f"\nViolation {i+1}:")
        print(f"  Type: {violation.violation_type}")
        print(f"  URL: {violation.post_url}")
        print(f"  Confidence: {violation.confidence:.2f}")
        print(f"  Evidence: {violation.evidence}")
    
    # Save results
    results_file = miner.save_results()
    print(f"\nResults saved to: {results_file}")

def example_2_focused_analysis():
    """Example 2: Focused analysis on specific violation types"""
    print("\n=== Example 2: Focused Analysis ===")
    
    # Custom config for focused analysis
    custom_config = {
        "vk": {
            "access_token": "your_token_here",
            "group_id": "dsmotopro"
        },
        "analysis": {
            "max_posts_per_scan": 200,
            "fraud_keywords": ["продам", "куплю", "цена", "договор", "официально", "реквизиты"],
            "violence_keywords": ["дтп", "авария", "наезд", "столкновение", "опасный"]
        }
    }
    
    # Save custom config
    config_path = Path("./config/custom_config.json")
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(custom_config, f, indent=2)
    
    # Initialize with custom config
    miner = LegalMiningVK(str(config_path))
    violations = miner.scan_group_wall(count=200)
    
    # Analyze by type
    duplicate_count = len([v for v in violations if v.violation_type == "duplicate_content"])
    fraud_count = len([v for v in violations if v.violation_type == "fraud_scam"])
    violence_count = len([v for v in violations if v.violation_type == "traffic_violence"])
    
    print(f"Duplicate content: {duplicate_count}")
    print(f"Fraud/Scam: {fraud_count}")
    print(f"Traffic violence: {violence_count}")
    
    # Get high confidence violations
    high_confidence = [v for v in violations if v.confidence >= 0.9]
    print(f"High confidence violations: {len(high_confidence)}")

def example_3_automated_reporting():
    """Example 3: Automated reporting with account rotation"""
    print("\n=== Example 3: Automated Reporting ===")
    
    # First, get violations from previous scan or load from file
    violations_file = Path("./data/results/violations_20240115_103000.json")
    
    if violations_file.exists():
        with open(violations_file, 'r') as f:
            violations_data = json.load(f)
        
        # Initialize report automation
        automation = VKReportAutomation()
        
        # Generate report requests
        report_requests = automation.generate_report_requests(violations_data["violations"])
        print(f"Generated {len(report_requests)} report requests")
        
        # Submit first 5 reports (example)
        sample_requests = report_requests[:5]
        results = automation.submit_bulk_reports(sample_requests)
        
        print(f"Submitted {results['successful']}/{results['total']} reports")
        if results['errors']:
            print(f"Errors: {results['errors']}")
    else:
        print("No violations file found. Run scan example first.")

def example_4_dmca_campaign():
    """Example 4: DMCA campaign for brand protection"""
    print("\n=== Example 4: DMCA Campaign ===")
    
    # Initialize support pressure module
    pressure = SupportPressure()
    
    # Sample violations data
    sample_violations = [
        {
            "post_url": "https://vk.com/wall-123456789_123456",
            "violation_type": "duplicate_content",
            "evidence": {
                "text_snippet": "Продам BMW X5, отличный состояние, цена договорная",
                "brand_detected": "BMW"
            }
        },
        {
            "post_url": "https://vk.com/wall-123456789_123457",
            "violation_type": "duplicate_content", 
            "evidence": {
                "text_snippet": "Mercedes-Benz E-Class, официальные реквизиты прилагаются",
                "brand_detected": "Mercedes"
            }
        }
    ]
    
    # Generate DMCA claims
    claims = pressure.generate_brand_protection_claims(sample_violations)
    print(f"Generated {len(claims)} DMCA claims")
    
    # Display claim details
    for claim in claims:
        print(f"\nClaim for {claim.brand_name}:")
        print(f"  Infringing URL: {claim.infringing_post_url}")
        print(f"  Copyright holder: {claim.copyright_holder}")
        print(f"  Claim ID: {claim.claim_id}")
    
    # Submit claims (commented out for example)
    # results = pressure.batch_submit_claims(claims)
    # print(f"Submitted {results['successful']}/{results['total']} claims")

def example_5_full_compliance_cycle():
    """Example 5: Full compliance cycle with monitoring"""
    print("\n=== Example 5: Full Compliance Cycle ===")
    
    # Initialize main system
    compliance = VKComplianceStrike()
    
    # Run full cycle with limited scope for example
    results = compliance.run_full_compliance_cycle(
        scan_posts=50,  # Limited for example
        submit_reports=False,  # Disabled for example
        submit_dmca=False,    # Disabled for example
        submit_tickets=False  # Disabled for example
    )
    
    # Display results
    print(f"Scan completed in {results.get('duration', 0):.2f} seconds")
    print(f"Violations found: {results['scan_results']['violations_found']}")
    
    # Show violation breakdown
    summary = results['scan_results']['violation_summary']
    print(f"By type: {summary['by_type']}")
    print(f"By content: {summary['by_content_type']}")
    print(f"High confidence: {summary['high_confidence']}")

def example_6_monitoring_dashboard():
    """Example 6: Simple monitoring dashboard"""
    print("\n=== Example 6: Monitoring Dashboard ===")
    
    # Load recent results
    results_dir = Path("./data/results")
    recent_files = sorted(results_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
    
    print("Recent Compliance Activity:")
    print("-" * 50)
    
    for file_path in recent_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            timestamp = data.get('timestamp', file_path.stem)
            if 'summary' in data:  # Full cycle results
                summary = data['summary']
                print(f"{timestamp}: {summary.get('total_violations', 0)} violations, "
                      f"{summary.get('reports_submitted', 0)} reports, "
                      f"{summary.get('success_rate', 0):.1f}% success")
            elif 'violations_found' in data:  # Scan only results
                print(f"{timestamp}: {data.get('violations_found', 0)} violations found")
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

def example_7_custom_brand_protection():
    """Example 7: Custom brand protection configuration"""
    print("\n=== Example 7: Custom Brand Protection ===")
    
    # Custom brand configuration
    brand_config = {
        "legal": {
            "default_copyright_holders": [
                "Tesla, Inc.",
                "Ford Motor Company",
                "General Motors"
            ],
            "brand_mapping": {
                "tesla": "Tesla, Inc.",
                "model s": "Tesla, Inc.",
                "ford": "Ford Motor Company",
                "mustang": "Ford Motor Company",
                "chevrolet": "General Motors",
                "cadillac": "General Motors"
            }
        }
    }
    
    # Sample violations with custom brands
    custom_violations = [
        {
            "post_url": "https://vk.com/wall-123456789_999999",
            "evidence": {
                "text_snippet": "Продам Tesla Model S 2021, отличный состояние"
            }
        }
    ]
    
    # Initialize with custom config
    pressure = SupportPressure()
    
    # Override brand mapping
    original_holders = pressure.config["legal"]["default_copyright_holders"]
    pressure.config["legal"]["default_copyright_holders"] = brand_config["legal"]["default_copyright_holders"]
    
    # Generate claims
    claims = pressure.generate_brand_protection_claims(custom_violations)
    
    for claim in claims:
        print(f"Custom claim for {claim.copyright_holder}")
        print(f"Content: {claim.content_description}")
        print(f"Contact: {claim.contact_email}")

def example_8_batch_processing():
    """Example 8: Batch processing multiple groups"""
    print("\n=== Example 8: Batch Processing ===")
    
    # Multiple groups to scan
    groups = ["dsmotopro", "auto_ru", "car_sales"]  # Example group IDs
    
    all_violations = []
    
    for group_id in groups:
        print(f"Scanning group: {group_id}")
        
        # Create config for specific group
        group_config = {
            "vk": {
                "access_token": "your_token_here",
                "group_id": group_id
            },
            "analysis": {
                "max_posts_per_scan": 50
            }
        }
        
        # Save temporary config
        config_path = Path(f"./config/temp_{group_id}.json")
        with open(config_path, 'w') as f:
            json.dump(group_config, f)
        
        # Scan group
        miner = LegalMiningVK(str(config_path))
        violations = miner.scan_group_wall(count=50)
        
        print(f"  Found {len(violations)} violations")
        all_violations.extend(violations)
        
        # Cleanup temp config
        config_path.unlink()
        
        # Rate limiting between groups
        time.sleep(5)
    
    print(f"\nTotal violations across all groups: {len(all_violations)}")
    
    # Save combined results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_file = Path(f"./data/results/combined_scan_{timestamp}.json")
    
    combined_data = {
        "timestamp": datetime.now().isoformat(),
        "groups_scanned": groups,
        "total_violations": len(all_violations),
        "violations": [
            {
                "post_id": v.post_id,
                "post_url": v.post_url,
                "violation_type": v.violation_type,
                "confidence": v.confidence,
                "evidence": v.evidence
            }
            for v in all_violations
        ]
    }
    
    with open(combined_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"Combined results saved to: {combined_file}")

def main():
    """Run all examples"""
    print("VK-COMPLIANCE-STRIKE Usage Examples")
    print("=" * 50)
    
    examples = [
        example_1_basic_scan,
        example_2_focused_analysis,
        example_3_automated_reporting,
        example_4_dmca_campaign,
        example_5_full_compliance_cycle,
        example_6_monitoring_dashboard,
        example_7_custom_brand_protection,
        example_8_batch_processing
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            print(f"\n{'='*20} Example {i} {'='*20}")
            example_func()
        except Exception as e:
            print(f"Example {i} failed: {e}")
        
        if i < len(examples):
            input("\nPress Enter to continue to next example...")
    
    print("\n" + "="*50)
    print("All examples completed!")

if __name__ == "__main__":
    main()
