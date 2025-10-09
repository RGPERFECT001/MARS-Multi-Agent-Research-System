"""Main execution script for the multi-agent research system."""

import logging
import argparse
import json
import os
from datetime import datetime
from workflow import MultiAgentResearchWorkflow
from config import REPORTS_DIR, LOGS_DIR, CS_IT_DOMAIN_ONLY
from gemini_client import gemini_client
from data_sources import CSResearchFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOGS_DIR}/research_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def save_report(report_data: dict, topic: str) -> str:
    """Save the final report to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{topic.replace(' ', '_')}_{timestamp}.json"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Report saved to: {filepath}")
    return filepath


def print_model_status():
    """Print the current status of all models."""
    print("\n" + "="*50)
    print("MODEL STATUS")
    print("="*50)
    
    status = gemini_client.get_model_status()
    for model_name, model_info in status.items():
        status_icon = "✅" if model_info["available"] else "❌"
        rate_limit_icon = "⏰" if model_info["rate_limited"] else "🟢"
        
        print(f"{status_icon} {model_name} (Priority: {model_info['priority']})")
        print(f"   Available: {model_info['available']} | Rate Limited: {model_info['rate_limited']}")
        print(f"   Errors: {model_info['error_count']} | Last Used: {model_info['last_used']}")
        print()


def print_report_summary(result: dict):
    """Print a summary of the research result."""
    print("\n" + "="*80)
    print("RESEARCH REPORT SUMMARY")
    print("="*80)
    
    print(f"Topic: {result.get('user_topic', 'N/A')}")
    print(f"Iterations: {result.get('current_iteration', 'N/A')}")
    print(f"Research Attempts: {result.get('research_attempts', 'N/A')}")
    print(f"Writing Attempts: {result.get('writing_attempts', 'N/A')}")
    
    if result.get('final_report'):
        print(f"\nReport Length: {len(result['final_report'])} characters")
        print("\nFinal Report Preview:")
        print("-" * 40)
        preview = result['final_report'][:500]
        print(preview)
        if len(result['final_report']) > 500:
            print("...")
    
    if result.get('error'):
        print(f"\nError: {result['error']}")
    
    print("="*80)


def progress_callback(message: str):
    """Callback function for progress updates."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def main():
    """Main function to run the research system."""
    parser = argparse.ArgumentParser(description="Multi-Agent Research System")
    parser.add_argument(
        "topic", 
        help="Research topic to investigate"
    )
    parser.add_argument(
        "--output", 
        "-o", 
        help="Output file path for the report (optional)"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--stream", 
        "-s", 
        action="store_true", 
        help="Enable streaming mode with progress updates"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show model status and exit"
    )
    parser.add_argument(
        "--reset-models",
        action="store_true",
        help="Reset all models to available status and exit"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle special commands
    if args.status:
        print_model_status()
        return 0
    
    if args.reset_models:
        print("Resetting all models to available status...")
        gemini_client.reset_all_models()
        print("✅ All models reset successfully")
        print_model_status()
        return 0
    
    print("CS/IT Multi-Agent Research System")
    print("=" * 50)
    print(f"Research Topic: {args.topic}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Validate CS/IT domain if enabled
    if CS_IT_DOMAIN_ONLY:
        fetcher = CSResearchFetcher()
        is_cs_it = fetcher.is_cs_it_topic(args.topic)
        
        if not is_cs_it:
            print("⚠️  Warning: Topic may not be CS/IT related")
            print("This system is specialized for Computer Science and Information Technology topics")
            print("Consider rephrasing your topic to focus on CS/IT aspects")
            print()
        
        print(f"CS/IT Domain Validation: {'✅' if is_cs_it else '⚠️'}")
        print()
    
    try:
        # Initialize the workflow
        workflow = MultiAgentResearchWorkflow()
        
        # Run the research workflow
        if args.stream:
            print("\nStarting research workflow with progress updates...")
            result = workflow.run_with_callback(args.topic, progress_callback)
        else:
            print("\nStarting research workflow...")
            result = workflow.run(args.topic)
        
        # Save the report
        if args.output:
            output_path = args.output
        else:
            output_path = save_report(result, args.topic)
        
        # Print summary
        print_report_summary(result)
        
        # Print model status
        print_model_status()
        
        print(f"\nReport saved to: {output_path}")
        
        # Print the full report if requested
        if result.get('final_report') and not args.output:
            print("\n" + "="*80)
            print("FULL REPORT")
            print("="*80)
            print(result['final_report'])
        
    except KeyboardInterrupt:
        print("\n\nResearch workflow interrupted by user.")
        logger.info("Research workflow interrupted by user")
    except Exception as e:
        print(f"\nError running research workflow: {e}")
        logger.error(f"Error running research workflow: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
