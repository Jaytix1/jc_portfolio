#!/usr/bin/env python
"""
HC_Pipeline CLI - Command-line interface for running the pipeline

Usage:
    python run_pipeline.py --job stocks    # Run stock price collection
    python run_pipeline.py --job news      # Run news collection
    python run_pipeline.py --job deals     # Run deals collection
    python run_pipeline.py --job ships     # Run ship spec collection
    python run_pipeline.py --job all       # Run all collectors
    python run_pipeline.py --status        # Show recent pipeline runs
"""

import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(
        description='HC_Pipeline - Cruise Data Collection Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --job stocks     Collect stock prices for CCL, RCL, NCLH
  python run_pipeline.py --job news       Collect news from RSS feeds
  python run_pipeline.py --job deals      Collect cruise deals
  python run_pipeline.py --job ships      Collect ship specifications
  python run_pipeline.py --job all        Run all collectors
  python run_pipeline.py --status         Show recent pipeline runs
        """
    )

    parser.add_argument(
        '--job', '-j',
        choices=['stocks', 'news', 'deals', 'ships', 'all'],
        help='Which collection job to run'
    )

    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show recent pipeline run status'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Must specify either --job or --status
    if not args.job and not args.status:
        parser.print_help()
        return 1

    # Import and create pipeline
    try:
        from HC_Pipeline.main import Pipeline
        pipeline = Pipeline()

        if args.status:
            status = pipeline.get_status()
            print("\nRecent Pipeline Runs:")
            print("-" * 70)
            for run in status['recent_runs']:
                status_icon = '[OK]' if run['status'] == 'success' else '[ERR]' if run['status'] == 'failed' else '[...]'
                print(f"  {status_icon:5} {run['type']:8} | {run['status']:8} | {run['started'][:19]} | +{run['records_added']} records")
                if run['error']:
                    print(f"    Error: {run['error'][:50]}...")
            print()
            return 0

        # Run the specified job
        if args.job == 'all':
            results = pipeline.run_all()
            success = all(results.values())
        elif args.job == 'stocks':
            success = pipeline.run_stocks()
        elif args.job == 'news':
            success = pipeline.run_news()
        elif args.job == 'deals':
            success = pipeline.run_deals()
        elif args.job == 'ships':
            success = pipeline.run_ships()
        else:
            print(f"Unknown job: {args.job}")
            return 1

        if success:
            print(f"\n[OK] Pipeline job '{args.job}' completed successfully")
            return 0
        else:
            print(f"\n[ERROR] Pipeline job '{args.job}' completed with errors")
            return 1

    except ImportError as e:
        print(f"Error: Missing required dependency - {e}")
        print("Run: pip install -r HC_Pipeline/requirements.txt")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
