from __future__ import annotations

import os
from typing import Dict, Any
import pandas as pd


def generate_plots(out_dir: str, results_df: pd.DataFrame) -> Dict[str, str]:
    """Generate plots for the backtest results."""
    plots = {}
    plots_dir = os.path.join(out_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        
        # Plot 1: Compound Score Over Time
        plt.figure(figsize=(12, 6))
        models = results_df["model"].unique()
        for model in models:
            model_data = results_df[results_df["model"] == model]
            plt.plot(model_data["window"], model_data["compound"], 
                    label=model, marker='o', markersize=3, alpha=0.7)
        
        plt.xlabel("Window")
        plt.ylabel("Compound Score")
        plt.title("Compound Score Over Time")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        compound_plot_path = os.path.join(plots_dir, "compound_over_time.png")
        plt.savefig(compound_plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        plots["compound_over_time"] = compound_plot_path
        
        # Plot 2: Hit Rate Comparison
        plt.figure(figsize=(10, 6))
        summary_data = []
        for model in models:
            model_data = results_df[results_df["model"] == model]
            hit_rates = {
                "Hit6": model_data["hit6"].mean(),
                "Hit5": model_data["hit5"].mean(), 
                "Hit4": model_data["hit4"].mean()
            }
            for hit_type, rate in hit_rates.items():
                summary_data.append({"Model": model, "Hit Type": hit_type, "Rate": rate})
        
        summary_df = pd.DataFrame(summary_data)
        pivot_df = summary_df.pivot(index="Model", columns="Hit Type", values="Rate")
        
        ax = pivot_df.plot(kind="bar", figsize=(10, 6))
        plt.title("Hit Rates by Model")
        plt.ylabel("Hit Rate")
        plt.xlabel("Model")
        plt.xticks(rotation=45)
        plt.legend(title="Hit Type")
        plt.grid(True, alpha=0.3)
        
        hit_rates_plot_path = os.path.join(plots_dir, "hit_rates.png")
        plt.savefig(hit_rates_plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        plots["hit_rates"] = hit_rates_plot_path
        
    except ImportError:
        print("⚠️ matplotlib not available, skipping plots")
    except Exception as e:
        print(f"⚠️ Error generating plots: {e}")
    
    return plots


def generate_report(out_dir: str) -> Dict[str, Any]:
    """Generate HTML report and plots for the backtest results."""
    
    # Load results if available
    results_path = os.path.join(out_dir, "backtest_results.csv")
    summary_path = os.path.join(out_dir, "summary.csv")
    args_path = os.path.join(out_dir, "args.json")
    
    plots = {}
    
    if os.path.exists(results_path):
        results_df = pd.read_csv(results_path)
        plots = generate_plots(out_dir, results_df)
    else:
        # Create minimal placeholder
        results_df = pd.DataFrame([])
    
    if os.path.exists(summary_path):
        summary_df = pd.read_csv(summary_path)
    else:
        summary_df = pd.DataFrame([{"model": "placeholder", "windows": 0, "mean_compound": 0.0}])
    
    # Load run arguments
    args = {}
    if os.path.exists(args_path):
        import json
        with open(args_path, 'r') as f:
            args = json.load(f)
    
    # Generate HTML report
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OMEGA Evaluation Harness Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; 
                   background: #f8f9fa; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .plot {{ text-align: center; margin: 20px 0; }}
        .plot img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
        .reproduce {{ background: #e8f4f8; padding: 15px; border-radius: 5px; 
                      font-family: monospace; margin: 20px 0; }}
        .args {{ background: #f8f9fa; padding: 10px; border-radius: 5px; 
                 font-family: monospace; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 OMEGA Evaluation Harness Report</h1>
        <p>Systematic backtesting results for lottery prediction models</p>
    </div>
    
    <div class="section">
        <h2>📊 Summary Metrics</h2>
        <div>
"""

    # Add summary metrics
    if len(summary_df) > 0:
        total_windows = summary_df["windows"].sum()
        best_model = summary_df.loc[summary_df["mean_compound"].idxmax(), "model"] if len(summary_df) > 0 else "None"
        best_score = summary_df["mean_compound"].max() if len(summary_df) > 0 else 0
        
        html_content += f"""
            <div class="metric">
                <div class="metric-value">{len(summary_df)}</div>
                <div class="metric-label">Models Tested</div>
            </div>
            <div class="metric">
                <div class="metric-value">{total_windows}</div>
                <div class="metric-label">Total Windows</div>
            </div>
            <div class="metric">
                <div class="metric-value">{best_model}</div>
                <div class="metric-label">Best Model</div>
            </div>
            <div class="metric">
                <div class="metric-value">{best_score:.3f}</div>
                <div class="metric-label">Best Score</div>
            </div>
        """
    
    html_content += """
        </div>
    </div>
    
    <div class="section">
        <h2>📈 Performance Summary</h2>
        <table>
            <tr>
                <th>Model</th>
                <th>Windows</th>
                <th>Mean Compound</th>
                <th>Hit6</th>
                <th>Hit5</th>
                <th>Hit4</th>
                <th>Total Points</th>
            </tr>
"""

    # Add summary table
    for _, row in summary_df.iterrows():
        html_content += f"""
            <tr>
                <td>{row.get('model', 'N/A')}</td>
                <td>{row.get('windows', 0)}</td>
                <td>{row.get('mean_compound', 0):.4f}</td>
                <td>{row.get('hit6_count', 0)}</td>
                <td>{row.get('hit5_count', 0)}</td>
                <td>{row.get('hit4_count', 0)}</td>
                <td>{row.get('total_points', 0):.1f}</td>
            </tr>
        """
    
    html_content += """
        </table>
    </div>
"""

    # Add plots
    if plots:
        html_content += """
    <div class="section">
        <h2>📊 Visualizations</h2>
"""
        for plot_name, plot_path in plots.items():
            plot_filename = os.path.basename(plot_path)
            html_content += f"""
        <div class="plot">
            <h3>{plot_name.replace('_', ' ').title()}</h3>
            <img src="plots/{plot_filename}" alt="{plot_name}">
        </div>
"""
        html_content += "</div>"
    
    # Reproduce section
    html_content += f"""
    <div class="section">
        <h2>🔄 Reproduce This Run</h2>
        <p>To reproduce these exact results, run the following command:</p>
        <div class="reproduce">
python -m tools.eval_harness.cli backtest \\<br>
&nbsp;&nbsp;--data {args.get('data_path', 'data/historial_kabala_github_fixed.csv')} \\<br>
&nbsp;&nbsp;--models {','.join(args.get('models', []))} \\<br>
&nbsp;&nbsp;--windows {args.get('windows', 'rolling_200')} \\<br>
&nbsp;&nbsp;--top_n {args.get('top_n', 10)} \\<br>
&nbsp;&nbsp;--seed {args.get('seed', 42)} \\<br>
&nbsp;&nbsp;--out {args.get('out_dir', 'results/accuracy_analysis/run_test')}
        </div>
        
        <h3>Run Arguments</h3>
        <div class="args">
{args}
        </div>
    </div>
    
    <div class="section">
        <h2>ℹ️ About This Report</h2>
        <p>This report was generated by the OMEGA Evaluation Harness, a systematic backtesting framework for lottery prediction models.</p>
        <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Framework:</strong> OMEGA_PRO_AI_v10.1</p>
    </div>
    
</body>
</html>
"""

    # Save HTML report
    html_path = os.path.join(out_dir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"📄 HTML report generated: {html_path}")
    
    return {
        "html_path": html_path,
        "plots": plots,
        "summary_rows": len(summary_df),
    }