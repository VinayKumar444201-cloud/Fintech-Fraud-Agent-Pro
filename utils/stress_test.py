import os
import time
import pandas as pd
from typing import List, Dict
from utils.chat_agent import ComplianceIntelligenceProvider
from utils.agents import ComplianceAuditEngine


class AuditStressTester:
    """
    Automated evaluation suite to benchmark the accuracy and
    reliability of the Forensic Audit Engine.
    """

    def __init__(self):
        self.rag_provider = ComplianceIntelligenceProvider()
        self.audit_engine = ComplianceAuditEngine()

        # Test Cases: Expected results for specific scenarios
        self.golden_set = [
            {
                "data": "ID: T101 | Amt: $50,000 | Country: Russia",
                "expected_verdict": "Suspicious",
                "reason": "Sanctioned jurisdiction"
            },
            {
                "data": "ID: T102 | Amt: $500 | Country: USA",
                "expected_verdict": "Clear",
                "reason": "Low value, stable jurisdiction"
            },
            {
                "data": "ID: T103 | Amt: $9,990 | Country: Cayman Islands",
                "expected_verdict": "Suspicious",
                "reason": "Structuring threshold and tax haven"
            }
        ]

    def run_benchmark(self):
        """Executes the test suite and calculates accuracy metrics."""
        print(f"\n{'=' * 50}")
        print("🚀 STARTING FORENSIC ENGINE BENCHMARK")
        print(f"{'=' * 50}\n")

        passed = 0
        total = len(self.golden_set)

        for i, test in enumerate(self.golden_set):
            print(f"Test {i + 1}/{total}: Testing {test['reason']}...")

            # Run the actual audit
            initial, verified = self.audit_engine.execute_verified_audit(
                test['data'],
                self.rag_provider.engine
            )

            # Check if the AI's verdict matches our expected verdict
            ai_verdict = "Suspicious" if "suspicious" in verified.lower() else "Clear"

            if ai_verdict == test['expected_verdict']:
                print(f"✅ Result: PASS (AI detected {ai_verdict})")
                passed += 1
            else:
                print(f"❌ Result: FAIL (AI detected {ai_verdict}, Expected {test['expected_verdict']})")

            print(f"AI Reasoning: {verified[:100]}...\n")
            time.sleep(1)  # Prevent rate limiting

        accuracy = (passed / total) * 100
        print(f"{'=' * 50}")
        print(f"BENCHMARK COMPLETE")
        print(f"Final Accuracy Score: {accuracy}%")
        print(f"{'=' * 50}\n")


if __name__ == "__main__":
    tester = AuditStressTester()
    tester.run_benchmark()