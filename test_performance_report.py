import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from modules.performance_reporter import generate_performance_dashboard

def test_performance_report_generation():
    try:
        print("🔍 Testing Performance Report Generation...")
        report_path = generate_performance_dashboard()
        
        if not report_path or not os.path.exists(report_path):
            print("❌ Performance report generation failed")
            sys.exit(1)
        
        print(f"✅ Performance report successfully generated: {report_path}")
        
        # Additional checks
        print("\n📊 Checking report details:")
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Report size: {len(content)} characters")
            
            # Basic content checks
            checks = [
                "OMEGA AI" in content,
                "Rendimiento" in content,
                "modelo" in content
            ]
            
            if all(checks):
                print("✅ Report contains expected content")
            else:
                print("❌ Report content seems incomplete")
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error in performance report generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_performance_report_generation()