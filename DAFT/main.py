#!/usr/bin/env python3
"""
EVENT_HORIZON — Defensive Authentication Resilience Framework (DARF)

Main CLI interface for running resilience assessments.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional
import structlog
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from core.engine import EventHorizonEngine
from core.scoring import ResilienceScorer
from core.reporting import ReportGenerator
from config.config_manager import ConfigManager
from config.scenarios import ScenarioLibrary


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
console = Console()


class EventHorizonCLI:
    """Command-line interface for EVENT_HORIZON framework"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.scenario_library = ScenarioLibrary()
        self.console = Console()
        
    async def run_assessment(self, 
                           config_file: str = "default.yaml",
                           components_file: str = "components.yaml",
                           scenarios: Optional[List[str]] = None,
                           output_dir: str = "reports") -> None:
        """
        Run a complete resilience assessment.
        
        Args:
            config_file: Configuration file path
            components_file: Components configuration file path
            scenarios: List of scenario IDs to run (None for comprehensive suite)
            output_dir: Output directory for reports
        """
        try:
            # Load configuration
            self.console.print("[bold blue]Loading configuration...[/bold blue]")
            config = self.config_manager.load_config(config_file)
            components = self.config_manager.load_components(components_file)
            
            # Initialize engine
            engine = EventHorizonEngine()
            
            # Register components
            for component in components.values():
                engine.register_component(component)
            
            # Select scenarios
            if scenarios:
                selected_scenarios = [self.scenario_library.get_scenario(sid) for sid in scenarios]
            else:
                selected_scenarios = self.scenario_library.get_comprehensive_suite()
            
            # Add scenarios to engine
            for scenario in selected_scenarios:
                engine.add_scenario(scenario)
            
            self.console.print(f"[bold green]Loaded {len(components)} components and {len(selected_scenarios)} scenarios[/bold green]")
            
            # Run assessment with progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Running resilience assessment...", total=None)
                
                results = await engine.run_assessment()
                
                progress.update(task, description="Calculating resilience scores...")
                
                # Calculate scores
                scorer = ResilienceScorer(config.scoring_weights)
                scores = scorer.calculate_resilience_scores(results)
                
                progress.update(task, description="Generating reports...")
                
                # Generate reports
                report_generator = ReportGenerator(output_dir)
                report_files = report_generator.generate_all_reports(results, scores)
            
            # Display results
            self._display_results(results, scores, report_files)
            
        except Exception as e:
            self.console.print(f"[bold red]Error: {str(e)}[/bold red]")
            logger.error("Assessment failed", error=str(e))
            sys.exit(1)
    
    def _display_results(self, results, scores, report_files):
        """Display assessment results"""
        # Get system score
        system_score = next((s for s in scores if s.component_id is None), None)
        
        if not system_score:
            self.console.print("[bold red]No system score calculated[/bold red]")
            return
        
        # Create summary panel
        summary_text = f"""
[bold]Overall Resilience Score:[/bold] {system_score.score:.3f}
[bold]Assessment Level:[/bold] {self._get_assessment_level(system_score.score)}
[bold]Confidence:[/bold] {system_score.confidence:.3f}

[bold]Test Summary:[/bold]
• Total Requests: {results.system_metrics.total_requests:,}
• Success Rate: {(results.system_metrics.total_requests - results.system_metrics.failed_requests) / results.system_metrics.total_requests:.2%}
• Average Response Time: {results.system_metrics.avg_response_time:.3f}s
• Throughput: {results.system_metrics.throughput:.2f} req/s
• Failure Events: {len(results.system_metrics.failure_events)}
• Semantic Drift Events: {len(results.semantic_drift_events)}
        """
        
        panel = Panel(summary_text.strip(), title="🎯 EVENT_HORIZON Assessment Results", border_style="green")
        self.console.print(panel)
        
        # Display score breakdown
        self._display_score_breakdown(system_score)
        
        # Display component scores
        self._display_component_scores(scores)
        
        # Display critical findings
        self._display_critical_findings(results, scores)
        
        # Display report files
        self._display_report_files(report_files)
    
    def _display_score_breakdown(self, system_score):
        """Display resilience score breakdown"""
        table = Table(title="Resilience Score Breakdown")
        table.add_column("Dimension", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Status", style="green")
        
        for dimension, score in system_score.breakdown.items():
            status = "✅ Good" if score >= 0.8 else "⚠️ Needs Attention" if score >= 0.6 else "❌ Poor"
            table.add_row(dimension.replace("_", " ").title(), f"{score:.3f}", status)
        
        self.console.print(table)
    
    def _display_component_scores(self, scores):
        """Display component-level scores"""
        component_scores = [s for s in scores if s.component_id is not None]
        
        if not component_scores:
            return
        
        table = Table(title="Component Resilience Scores")
        table.add_column("Component", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Assessment", style="green")
        table.add_column("Confidence", style="blue")
        
        # Sort by score (lowest first)
        component_scores.sort(key=lambda x: x.score)
        
        for score in component_scores:
            assessment = self._get_assessment_level(score.score)
            table.add_row(
                score.component_id,
                f"{score.score:.3f}",
                assessment,
                f"{score.confidence:.3f}"
            )
        
        self.console.print(table)
    
    def _display_critical_findings(self, results, scores):
        """Display critical findings"""
        findings = []
        
        # High error rate
        if results.system_metrics.error_rate > 0.1:
            findings.append(f"🔴 High system error rate: {results.system_metrics.error_rate:.2%}")
        
        # Slow response time
        if results.system_metrics.avg_response_time > 0.5:
            findings.append(f"🔴 Slow average response time: {results.system_metrics.avg_response_time:.3f}s")
        
        # Semantic drift
        if len(results.semantic_drift_events) > 0:
            avg_drift = sum(e.drift_magnitude for e in results.semantic_drift_events) / len(results.semantic_drift_events)
            findings.append(f"🔴 Semantic drift detected: {avg_drift:.3f} average magnitude")
        
        # Critical components
        system_score = next((s for s in scores if s.component_id is None), None)
        if system_score and system_score.score < 0.6:
            findings.append("🔴 Overall system resilience is CRITICAL")
        
        component_scores = [s for s in scores if s.component_id is not None]
        critical_components = [s for s in component_scores if s.score < 0.6]
        if critical_components:
            findings.append(f"🔴 Critical components: {', '.join(c.component_id for c in critical_components)}")
        
        if findings:
            panel = Panel("\n".join(findings), title="⚠️ Critical Findings", border_style="red")
            self.console.print(panel)
        else:
            self.console.print("[bold green]✅ No critical issues detected[/bold green]")
    
    def _display_report_files(self, report_files):
        """Display generated report files"""
        table = Table(title="Generated Reports")
        table.add_column("Report Type", style="cyan")
        table.add_column("File", style="magenta")
        
        for report_type, file_path in report_files.items():
            file_name = Path(file_path).name
            table.add_row(report_type.replace("_", " ").title(), file_name)
        
        self.console.print(table)
    
    def _get_assessment_level(self, score):
        """Get assessment level based on score"""
        if score >= 0.9:
            return "🟢 EXCELLENT"
        elif score >= 0.8:
            return "🟡 GOOD"
        elif score >= 0.7:
            return "🟡 ACCEPTABLE"
        elif score >= 0.6:
            return "🟠 NEEDS IMPROVEMENT"
        elif score >= 0.4:
            return "🔴 POOR"
        else:
            return "🔴 CRITICAL"
    
    def list_scenarios(self):
        """List all available scenarios"""
        scenarios = self.scenario_library.list_scenarios()
        
        table = Table(title="Available Test Scenarios")
        table.add_column("Scenario ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Description", style="white")
        
        for scenario_id in scenarios:
            scenario = self.scenario_library.get_scenario(scenario_id)
            table.add_row(scenario_id, scenario.name, scenario.description)
        
        self.console.print(table)
    
    def list_components(self, components_file: str = "components.yaml"):
        """List configured components"""
        try:
            components = self.config_manager.load_components(components_file)
            
            table = Table(title="Configured Components")
            table.add_column("Component ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Type", style="white")
            table.add_column("Endpoint", style="blue")
            table.add_column("Dependencies", style="green")
            
            for component in components.values():
                deps = ", ".join(component.dependencies) if component.dependencies else "None"
                table.add_row(
                    component.id,
                    component.name,
                    component.type.value,
                    component.endpoint,
                    deps
                )
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[bold red]Error loading components: {str(e)}[/bold red]")
    
    def create_sample_config(self):
        """Create sample configuration files"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Create default config
        default_config = {
            "max_concurrent_requests": 100,
            "test_timeout_seconds": 300,
            "log_level": "INFO",
            "output_directory": "reports",
            "enable_visualizations": True,
            "nsl_config": {
                "enable_utf8_tests": True,
                "enable_unicode_tests": True,
                "malformed_payload_ratio": 0.3
            },
            "scs_config": {
                "max_sessions": 10000,
                "session_ttl": 3600,
                "cleanup_interval": 300
            },
            "rlpm_config": {
                "ip_limit": 100,
                "user_limit": 50,
                "global_limit": 10000
            },
            "dbsil_config": {
                "max_connections": 100,
                "query_timeout": 30,
                "connection_pool_size": 100
            },
            "scoring_weights": {
                "availability": 0.25,
                "performance": 0.20,
                "consistency": 0.20,
                "security": 0.15,
                "recovery": 0.20
            }
        }
        
        config_file = config_dir / "default.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        # Create default components
        default_components = self.config_manager._get_default_components()
        self.config_manager.components = default_components
        self.config_manager.save_components("components.yaml")
        
        self.console.print("[bold green]Sample configuration files created in config/ directory[/bold green]")


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="EVENT_HORIZON — Defensive Authentication Resilience Framework (DARF)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run                                    # Run comprehensive assessment
  %(prog)s run --scenarios baseline_performance high_load_stress
  %(prog)s run --config custom.yaml --components custom_components.yaml
  %(prog)s list-scenarios                        # List available scenarios
  %(prog)s list-components                       # List configured components
  %(prog)s create-config                         # Create sample configuration
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run assessment command
    run_parser = subparsers.add_parser("run", help="Run resilience assessment")
    run_parser.add_argument("--config", default="default.yaml", help="Configuration file")
    run_parser.add_argument("--components", default="components.yaml", help="Components configuration file")
    run_parser.add_argument("--scenarios", nargs="+", help="Specific scenarios to run")
    run_parser.add_argument("--output", default="reports", help="Output directory for reports")
    
    # List scenarios command
    list_parser = subparsers.add_parser("list-scenarios", help="List available test scenarios")
    
    # List components command
    components_parser = subparsers.add_parser("list-components", help="List configured components")
    components_parser.add_argument("--file", default="components.yaml", help="Components configuration file")
    
    # Create config command
    config_parser = subparsers.add_parser("create-config", help="Create sample configuration files")
    
    return parser


async def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = EventHorizonCLI()
    
    if args.command == "run":
        await cli.run_assessment(
            config_file=args.config,
            components_file=args.components,
            scenarios=args.scenarios,
            output_dir=args.output
        )
    elif args.command == "list-scenarios":
        cli.list_scenarios()
    elif args.command == "list-components":
        cli.list_components(args.file)
    elif args.command == "create-config":
        cli.create_sample_config()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
