from __future__ import annotations

import argparse
import os
from typing import List

from .utils import ensure_dir, timestamped_run_dir
from .backtest import run_backtest
from .report import generate_report


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog="omega-eval", description="OMEGA Evaluation Harness")
    sub = parser.add_subparsers(dest="command", required=True)

    # Backtest command
    p_back = sub.add_parser("backtest", help="Run rolling-window backtest")
    p_back.add_argument("--data", required=True, help="Path to CSV dataset")
    p_back.add_argument("--models", required=True, help="Comma-separated model list")
    p_back.add_argument("--windows", default="rolling_200", help="Window configuration (e.g. rolling_200)")
    p_back.add_argument("--top_n", type=int, default=10, help="Number of predictions per model")
    p_back.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    p_back.add_argument("--out", default="results/accuracy_analysis/run_test", help="Output directory base")

    # Report command (optional standalone)
    p_report = sub.add_parser("report", help="Generate report from existing results")
    p_report.add_argument("--run_dir", required=True, help="Path to existing run directory")

    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    """Main CLI entry point."""
    args = parse_args(argv)
    
    if args.command == "backtest":
        # Create timestamped run directory
        run_dir = timestamped_run_dir(args.out)
        print(f"🚀 Starting backtest evaluation in: {run_dir}")
        
        # Parse models list
        models = [m.strip() for m in args.models.split(",")]
        print(f"🔧 Models to test: {models}")
        
        # Run backtest
        try:
            result = run_backtest(
                data_path=args.data,
                models=models,
                windows=args.windows,
                top_n=args.top_n,
                seed=args.seed,
                out_dir=run_dir,
            )
            
            if result.get("success"):
                print(f"✅ Backtest completed successfully!")
                print(f"📊 Processed {result['windows_processed']} windows")
                print(f"📈 Generated {result['total_results']} results")
                
                # Generate report
                print("📄 Generating report...")
                report_result = generate_report(run_dir)
                print(f"📋 Report saved: {report_result['html_path']}")
                
                return 0
            else:
                print(f"❌ Backtest failed: {result.get('error', 'Unknown error')}")
                return 1
                
        except Exception as e:
            print(f"💥 Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    elif args.command == "report":
        # Generate report from existing run
        if not os.path.exists(args.run_dir):
            print(f"❌ Run directory not found: {args.run_dir}")
            return 1
        
        try:
            print(f"📄 Generating report for: {args.run_dir}")
            report_result = generate_report(args.run_dir)
            print(f"✅ Report generated: {report_result['html_path']}")
            return 0
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return 1
    
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    exit(main())