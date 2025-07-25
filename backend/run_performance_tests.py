#!/usr/bin/env python3
"""
Comprehensive test runner for Runner Attendance Tracker
Executes all test types: unit, integration, WebSocket, QR code, load testing, and e2e
"""

import subprocess
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
import argparse


class TestRunner:
    """Orchestrates all testing scenarios"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Dict] = {}
        self.backend_dir = Path(__file__).parent
        self.frontend_dir = self.backend_dir.parent / "frontend"
        self.e2e_dir = self.backend_dir.parent / "e2e-tests"
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> Dict:
        """Run command and return result"""
        if cwd is None:
            cwd = self.backend_dir
        
        self.log(f"Running: {' '.join(cmd)} in {cwd}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            end_time = time.time()
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": end_time - start_time
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "duration": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": 0
            }
    
    def run_backend_unit_tests(self) -> bool:
        """Run backend unit tests with pytest"""
        self.log("Running backend unit tests...")
        
        cmd = ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
        if not self.verbose:
            cmd.extend(["-q"])
        
        result = self.run_command(cmd)
        self.results["backend_unit_tests"] = result
        
        if result["success"]:
            self.log("Backend unit tests PASSED")
        else:
            self.log(f"Backend unit tests FAILED: {result['stderr']}", "ERROR")
        
        return result["success"]
    
    def run_websocket_integration_tests(self) -> bool:
        """Run WebSocket integration tests"""
        self.log("Running WebSocket integration tests...")
        
        cmd = ["python", "-m", "pytest", "tests/test_websocket_integration.py", "-v"]
        if not self.verbose:
            cmd.extend(["-q"])
        
        result = self.run_command(cmd)
        self.results["websocket_tests"] = result
        
        if result["success"]:
            self.log("WebSocket integration tests PASSED")
        else:
            self.log(f"WebSocket integration tests FAILED: {result['stderr']}", "ERROR")
        
        return result["success"]
    
    def run_qr_integration_tests(self) -> bool:
        """Run QR code integration tests"""
        self.log("Running QR code integration tests...")
        
        cmd = ["python", "-m", "pytest", "tests/test_qr_integration.py", "-v"]
        if not self.verbose:
            cmd.extend(["-q"])
        
        result = self.run_command(cmd)
        self.results["qr_tests"] = result
        
        if result["success"]:
            self.log("QR code integration tests PASSED")
        else:
            self.log(f"QR code integration tests FAILED: {result['stderr']}", "ERROR")
        
        return result["success"]
    
    def run_frontend_unit_tests(self) -> bool:
        """Run frontend unit tests with Jest"""
        self.log("Running frontend unit tests...")
        
        # Check if frontend directory exists
        if not self.frontend_dir.exists():
            self.log("Frontend directory not found, skipping frontend tests", "WARNING")
            return True
        
        cmd = ["npm", "test", "--", "--watchAll=false", "--coverage"]
        result = self.run_command(cmd, cwd=self.frontend_dir)
        self.results["frontend_unit_tests"] = result
        
        if result["success"]:
            self.log("Frontend unit tests PASSED")
        else:
            self.log(f"Frontend unit tests FAILED: {result['stderr']}", "ERROR")
        
        return result["success"]
    
    def run_load_tests(self, scenario: str = "basic", users: int = 10) -> bool:
        """Run load tests with Locust"""
        self.log(f"Running load tests: {scenario} scenario with {users} users...")
        
        # Check if locust is available
        check_cmd = ["python", "-c", "import locust"]
        check_result = self.run_command(check_cmd)
        
        if not check_result["success"]:
            self.log("Locust not available, skipping load tests", "WARNING")
            return True
        
        # Run load test
        cmd = [
            "python", "performance_tests/test_runner.py", 
            scenario, str(users), "60s"
        ]
        
        result = self.run_command(cmd, timeout=120)
        self.results[f"load_test_{scenario}"] = result
        
        if result["success"]:
            self.log(f"Load test ({scenario}) PASSED")
        else:
            self.log(f"Load test ({scenario}) FAILED: {result['stderr']}", "ERROR")
        
        return result["success"]
    
    def run_e2e_tests(self) -> bool:
        """Run end-to-end tests with Playwright"""
        self.log("Running end-to-end tests...")
        
        # Check if Playwright is available
        if not (self.backend_dir.parent / "playwright.config.ts").exists():
            self.log("Playwright config not found, skipping e2e tests", "WARNING")
            return True
        
        cmd = ["npx", "playwright", "test", "--reporter=line"]
        if not self.verbose:
            cmd.append("--quiet")
        
        result = self.run_command(cmd, cwd=self.backend_dir.parent, timeout=600)
        self.results["e2e_tests"] = result
        
        if result["success"]:
            self.log("End-to-end tests PASSED")
        else:
            self.log(f"End-to-end tests FAILED: {result['stderr']}", "ERROR")
        
        return result["success"]
    
    def run_cross_browser_tests(self) -> bool:
        """Run cross-browser compatibility tests"""
        self.log("Running cross-browser tests...")
        
        browsers = ["chromium", "firefox", "webkit"]
        all_passed = True
        
        for browser in browsers:
            self.log(f"Testing browser: {browser}")
            
            cmd = ["npx", "playwright", "test", f"--project={browser}", "--reporter=line"]
            result = self.run_command(cmd, cwd=self.backend_dir.parent, timeout=300)
            
            self.results[f"browser_test_{browser}"] = result
            
            if result["success"]:
                self.log(f"Browser test ({browser}) PASSED")
            else:
                self.log(f"Browser test ({browser}) FAILED: {result['stderr']}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def run_mobile_tests(self) -> bool:
        """Run mobile compatibility tests"""
        self.log("Running mobile compatibility tests...")
        
        mobile_projects = ["Mobile Chrome", "Mobile Safari"]
        all_passed = True
        
        for project in mobile_projects:
            self.log(f"Testing mobile: {project}")
            
            cmd = ["npx", "playwright", "test", f"--project={project}", "--reporter=line"]
            result = self.run_command(cmd, cwd=self.backend_dir.parent, timeout=300)
            
            self.results[f"mobile_test_{project.lower().replace(' ', '_')}"] = result
            
            if result["success"]:
                self.log(f"Mobile test ({project}) PASSED")
            else:
                self.log(f"Mobile test ({project}) FAILED: {result['stderr']}", "ERROR")
                all_passed = False
        
        return all_passed
    
    def run_performance_benchmarks(self) -> bool:
        """Run performance benchmark tests"""
        self.log("Running performance benchmarks...")
        
        # Test different load scenarios
        scenarios = [
            ("basic", 10),
            ("peak", 50),
            ("stress", 100)
        ]
        
        all_passed = True
        
        for scenario, users in scenarios:
            success = self.run_load_tests(scenario, users)
            if not success:
                all_passed = False
        
        return all_passed
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(result["duration"] for result in self.results.values())
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration
            },
            "results": self.results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = "test_report.json"):
        """Save test report to file"""
        report_path = self.backend_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Test report saved to {report_path}")
    
    def print_summary(self, report: Dict):
        """Print test summary"""
        summary = report["summary"]
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        print("="*60)
        
        # Print failed tests
        if summary['failed'] > 0:
            print("\nFAILED TESTS:")
            for test_name, result in report["results"].items():
                if not result["success"]:
                    print(f"  ❌ {test_name}: {result['stderr'][:100]}...")
        
        print(f"\nDetailed report saved to test_report.json")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quick", "-q", action="store_true", help="Run only essential tests")
    parser.add_argument("--load-only", action="store_true", help="Run only load tests")
    parser.add_argument("--e2e-only", action="store_true", help="Run only e2e tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose)
    
    runner.log("Starting comprehensive test suite...")
    
    # Determine which tests to run
    if args.unit_only:
        tests_to_run = [
            ("Backend Unit Tests", runner.run_backend_unit_tests),
            ("Frontend Unit Tests", runner.run_frontend_unit_tests),
            ("WebSocket Integration Tests", runner.run_websocket_integration_tests),
            ("QR Code Integration Tests", runner.run_qr_integration_tests),
        ]
    elif args.load_only:
        tests_to_run = [
            ("Load Tests", lambda: runner.run_performance_benchmarks()),
        ]
    elif args.e2e_only:
        tests_to_run = [
            ("End-to-End Tests", runner.run_e2e_tests),
            ("Cross-Browser Tests", runner.run_cross_browser_tests),
            ("Mobile Tests", runner.run_mobile_tests),
        ]
    elif args.quick:
        tests_to_run = [
            ("Backend Unit Tests", runner.run_backend_unit_tests),
            ("WebSocket Integration Tests", runner.run_websocket_integration_tests),
            ("QR Code Integration Tests", runner.run_qr_integration_tests),
            ("Basic Load Test", lambda: runner.run_load_tests("basic", 10)),
        ]
    else:
        # Full test suite
        tests_to_run = [
            ("Backend Unit Tests", runner.run_backend_unit_tests),
            ("Frontend Unit Tests", runner.run_frontend_unit_tests),
            ("WebSocket Integration Tests", runner.run_websocket_integration_tests),
            ("QR Code Integration Tests", runner.run_qr_integration_tests),
            ("Performance Benchmarks", runner.run_performance_benchmarks),
            ("End-to-End Tests", runner.run_e2e_tests),
            ("Cross-Browser Tests", runner.run_cross_browser_tests),
            ("Mobile Tests", runner.run_mobile_tests),
        ]
    
    # Run all tests
    overall_success = True
    
    for test_name, test_func in tests_to_run:
        runner.log(f"Starting: {test_name}")
        try:
            success = test_func()
            if not success:
                overall_success = False
        except Exception as e:
            runner.log(f"Error in {test_name}: {e}", "ERROR")
            overall_success = False
    
    # Generate and save report
    report = runner.generate_report()
    runner.save_report(report)
    runner.print_summary(report)
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()