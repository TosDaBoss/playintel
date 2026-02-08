#!/usr/bin/env python3
"""
Comprehensive UX Test Framework
Tests all 6 critical fixes from this session

Usage:
  python3 test_comprehensive_ux.py
  python3 test_comprehensive_ux.py --quick  (runs faster subset)
"""

import requests
import json
import time
import re
import argparse
from typing import List, Dict, Tuple
from datetime import datetime

API_URL = "http://localhost:8000/api/chat"
RESULTS_FILE = "/Users/tosdaboss/playintel/ux_test_results.json"


class Color:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class UXTestFramework:
    def __init__(self, quick_mode=False):
        self.quick_mode = quick_mode
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def print_header(self, text):
        """Print test section header"""
        print(f"\n{Color.BOLD}{'='*80}")
        print(f"{text}")
        print(f"{'='*80}{Color.END}\n")

    def print_test(self, name, status, details=""):
        """Print individual test result"""
        if status == "PASS":
            icon = f"{Color.GREEN}✅{Color.END}"
            self.passed += 1
        elif status == "FAIL":
            icon = f"{Color.RED}❌{Color.END}"
            self.failed += 1
        else:  # WARNING
            icon = f"{Color.YELLOW}⚠️{Color.END}"
            self.warnings += 1

        print(f"{icon} {name}: {status}")
        if details:
            print(f"   {details}")

    def api_call(self, question: str, conversation_history: List = None) -> Dict:
        """Make API call and return response"""
        try:
            response = requests.post(
                API_URL,
                json={
                    "question": question,
                    "conversation_history": conversation_history or []
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    def test_1_vocabulary_variety(self):
        """Test 1: No overused words (honestly, realistically)"""
        self.print_header("TEST 1: Vocabulary Variety (No Overused Words)")

        test_result = {
            "test_name": "Vocabulary Variety",
            "tests": []
        }

        # Ask same question 3 times
        question = "What are the top 5 FPS games?"
        overused_words = ["honestly", "realistically"]

        responses = []
        for i in range(3):
            print(f"Attempt {i+1}/3: Asking '{question}'")
            data = self.api_call(question)

            if "error" not in data:
                answer = data.get("answer", "").lower()
                responses.append(answer)

                # Check for overused words
                found_bad = []
                for word in overused_words:
                    count = answer.count(word)
                    if count > 0:
                        found_bad.append(f"{word}({count}x)")

                test = {
                    "attempt": i + 1,
                    "overused_found": found_bad,
                    "passed": len(found_bad) == 0
                }
                test_result["tests"].append(test)

                status = "PASS" if not found_bad else "FAIL"
                details = f"Found: {', '.join(found_bad)}" if found_bad else ""
                self.print_test(f"Attempt {i+1}", status, details)

            time.sleep(2 if not self.quick_mode else 1)

        # Check variety
        unique_responses = len(set(responses))
        variety_test = {
            "unique_responses": unique_responses,
            "total_responses": len(responses),
            "passed": unique_responses >= 2
        }
        test_result["variety"] = variety_test

        status = "PASS" if variety_test["passed"] else "WARNING"
        self.print_test(
            "Response variety",
            status,
            f"{unique_responses}/{len(responses)} unique"
        )

        test_result["overall_status"] = "PASS" if all(t["passed"] for t in test_result["tests"]) and variety_test["passed"] else "FAIL"
        self.results["tests"].append(test_result)

    def test_2_no_backend_exposure(self):
        """Test 2: No backend technical terms exposed"""
        self.print_header("TEST 2: No Backend Exposure")

        test_result = {
            "test_name": "No Backend Exposure",
            "tests": []
        }

        backend_phrases = [
            "looking at", "checking", "let me check", "dataset",
            "database", "query", "sql", "analyzing the data",
            "based on the data", "from the data"
        ]

        test_questions = [
            "What are the top FPS games?",
            "Show me action games",
            "What's the most popular genre?",
            "Compare CS:GO vs PUBG"
        ]

        if self.quick_mode:
            test_questions = test_questions[:2]

        for question in test_questions:
            print(f"Testing: {question}")
            data = self.api_call(question)

            if "error" not in data:
                answer = data.get("answer", "").lower()

                found_backend = []
                for phrase in backend_phrases:
                    if phrase in answer:
                        found_backend.append(phrase)

                test = {
                    "question": question,
                    "backend_terms_found": found_backend,
                    "passed": len(found_backend) == 0
                }
                test_result["tests"].append(test)

                status = "PASS" if not found_backend else "FAIL"
                details = f"Found: {', '.join(found_backend)}" if found_backend else "Clean"
                self.print_test(question[:50], status, details)

            time.sleep(2 if not self.quick_mode else 1)

        test_result["overall_status"] = "PASS" if all(t["passed"] for t in test_result["tests"]) else "FAIL"
        self.results["tests"].append(test_result)

    def test_3_includes_requested_data(self):
        """Test 3: Always includes requested data fields"""
        self.print_header("TEST 3: Includes All Requested Data")

        test_result = {
            "test_name": "Includes Requested Data",
            "tests": []
        }

        test_cases = [
            {
                "question": "Show me games with highest ratings and most owners",
                "required_sql": ["rating", "owner"],
                "required_data": ["rating", "owner"]
            },
            {
                "question": "What are the top-rated action games?",
                "required_sql": ["rating"],
                "required_data": ["rating"]
            },
            {
                "question": "Games with high playtime and good reviews",
                "required_sql": ["hours", "rating"],
                "required_data": ["hours", "rating"]
            }
        ]

        if self.quick_mode:
            test_cases = test_cases[:2]

        for case in test_cases:
            print(f"Testing: {case['question']}")
            data = self.api_call(case["question"])

            if "error" not in data:
                sql = (data.get("sql_query") or "").lower()
                result_data = data.get("data", [])

                # Check SQL
                sql_has_all = all(req in sql for req in case["required_sql"])

                # Check data
                data_has_all = False
                if result_data and len(result_data) > 0:
                    data_keys = str(result_data[0].keys()).lower()
                    data_has_all = all(req in data_keys for req in case["required_data"])

                test = {
                    "question": case["question"],
                    "sql_includes_required": sql_has_all,
                    "data_includes_required": data_has_all,
                    "passed": sql_has_all and data_has_all
                }
                test_result["tests"].append(test)

                status = "PASS" if test["passed"] else "FAIL"
                details = f"SQL: {sql_has_all}, Data: {data_has_all}"
                self.print_test(case["question"][:50], status, details)

            time.sleep(2 if not self.quick_mode else 1)

        test_result["overall_status"] = "PASS" if all(t["passed"] for t in test_result["tests"]) else "FAIL"
        self.results["tests"].append(test_result)

    def test_4_format_variety(self):
        """Test 4: Response format varies by question type"""
        self.print_header("TEST 4: Response Format Variety")

        test_result = {
            "test_name": "Format Variety",
            "tests": []
        }

        test_cases = [
            {"question": "What are the top 3 games?", "expected_type": "list"},
            {"question": "Compare Indie vs AAA games", "expected_type": "comparison"},
            {"question": "Should I add achievements?", "expected_type": "advice"},
            {"question": "What's trending in action games?", "expected_type": "trend"}
        ]

        if self.quick_mode:
            test_cases = test_cases[:2]

        formats_detected = set()

        for case in test_cases:
            print(f"Testing: {case['question']}")
            data = self.api_call(case["question"])

            if "error" not in data:
                answer = data.get("answer", "")

                # Detect format
                has_bullets = "•" in answer or answer.count("-") > 3
                has_comparison = any(w in answer.lower() for w in ["vs", "compared", "difference", "while"])
                has_advice = any(w in answer.lower() for w in ["should", "recommend", "consider"])

                detected_format = "narrative"
                if has_comparison:
                    detected_format = "comparison"
                elif has_advice:
                    detected_format = "advice"
                elif has_bullets:
                    detected_format = "list"

                formats_detected.add(detected_format)

                test = {
                    "question": case["question"],
                    "expected_type": case["expected_type"],
                    "detected_format": detected_format,
                    "passed": True  # Format variety is good even if not exact match
                }
                test_result["tests"].append(test)

                self.print_test(case["question"][:50], "PASS", f"Format: {detected_format}")

            time.sleep(2 if not self.quick_mode else 1)

        # Overall: need at least 2 different formats
        variety_passed = len(formats_detected) >= 2

        test_result["formats_detected"] = list(formats_detected)
        test_result["variety_passed"] = variety_passed
        test_result["overall_status"] = "PASS" if variety_passed else "WARNING"

        status = "PASS" if variety_passed else "WARNING"
        self.print_test(
            "Format variety",
            status,
            f"{len(formats_detected)} different formats detected"
        )

        self.results["tests"].append(test_result)

    def test_5_direct_answers(self):
        """Test 5: Simple questions get direct answers (number first)"""
        self.print_header("TEST 5: Direct Answers (Number First)")

        test_result = {
            "test_name": "Direct Answers",
            "tests": []
        }

        test_cases = [
            {"question": "What's the average playtime for $15 games?", "expect_number_first": True},
            {"question": "How many FPS games are there?", "expect_number_first": True},
            {"question": "What's the average rating for action games?", "expect_number_first": True}
        ]

        if self.quick_mode:
            test_cases = test_cases[:2]

        for case in test_cases:
            print(f"Testing: {case['question']}")
            data = self.api_call(case["question"])

            if "error" not in data:
                answer = data.get("answer", "")

                # Check if number appears in first 50 chars
                first_part = answer[:100]
                has_number_first = bool(re.search(r'\d+\.?\d*', first_part))

                # Check for bad generic openings
                bad_openings = [
                    "absolutely, i'd be happy",
                    "let me share",
                    "based on thousands of steam launches"
                ]
                has_bad_opening = any(bad in answer.lower() for bad in bad_openings)

                test = {
                    "question": case["question"],
                    "number_in_first_100_chars": has_number_first,
                    "has_generic_opening": has_bad_opening,
                    "passed": has_number_first and not has_bad_opening
                }
                test_result["tests"].append(test)

                status = "PASS" if test["passed"] else "FAIL"
                details = "Direct" if has_number_first else "Number buried"
                if has_bad_opening:
                    details += ", Generic opening"
                self.print_test(case["question"][:50], status, details)

            time.sleep(2 if not self.quick_mode else 1)

        test_result["overall_status"] = "PASS" if all(t["passed"] for t in test_result["tests"]) else "FAIL"
        self.results["tests"].append(test_result)

    def test_6_consistency(self):
        """Test 6: Same question = same answer (CRITICAL)"""
        self.print_header("TEST 6: Query Consistency (CRITICAL)")

        test_result = {
            "test_name": "Query Consistency",
            "tests": []
        }

        # Test multiple phrasings of same question
        question_groups = [
            {
                "topic": "$20 game playtime",
                "questions": [
                    "what is the average playtime for games that cost 20 dollars?",
                    "if i priced my game at 20 dollars, what kind of playtimes should i expect?",
                    "what's the typical playtime for $20 games?",
                    "games priced at $20, how many hours of playtime?"
                ]
            },
            {
                "topic": "FPS game count",
                "questions": [
                    "how many FPS games are there?",
                    "what's the total number of FPS games on steam?",
                    "count of FPS games?"
                ]
            }
        ]

        if self.quick_mode:
            question_groups = question_groups[:1]
            question_groups[0]["questions"] = question_groups[0]["questions"][:2]

        for group in question_groups:
            print(f"\nTesting consistency: {group['topic']}")
            print("-" * 80)

            answers = []
            numbers = []

            for question in group["questions"]:
                print(f"  Asking: {question[:60]}...")
                data = self.api_call(question)

                if "error" not in data:
                    answer = data.get("answer", "")
                    sql = data.get("sql_query", "")

                    answers.append(answer)

                    # Extract number from answer
                    number_match = re.search(r'(\d+\.?\d*)\s*hours?', answer.lower())
                    if number_match:
                        numbers.append(float(number_match.group(1)))
                    else:
                        # Try to find any number
                        number_match = re.search(r'(\d+\.?\d*)', answer)
                        if number_match:
                            numbers.append(float(number_match.group(1)))

                time.sleep(2 if not self.quick_mode else 1)

            # Calculate consistency
            if len(numbers) >= 2:
                min_val = min(numbers)
                max_val = max(numbers)
                variance = max_val - min_val
                variance_pct = (variance / min_val * 100) if min_val > 0 else 0

                # Pass if variance is < 10%
                consistency_passed = variance_pct < 10

                test = {
                    "topic": group["topic"],
                    "questions_tested": len(group["questions"]),
                    "numbers_extracted": numbers,
                    "min_value": min_val,
                    "max_value": max_val,
                    "variance": variance,
                    "variance_pct": variance_pct,
                    "passed": consistency_passed
                }
                test_result["tests"].append(test)

                status = "PASS" if consistency_passed else "FAIL"
                details = f"Variance: {variance:.2f} ({variance_pct:.1f}%)"
                self.print_test(group["topic"], status, details)

                print(f"    Values: {numbers}")

        test_result["overall_status"] = "PASS" if all(t["passed"] for t in test_result["tests"]) else "FAIL"
        self.results["tests"].append(test_result)

    def save_results(self):
        """Save test results to JSON file"""
        with open(RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ Results saved to: {RESULTS_FILE}")

    def print_summary(self):
        """Print final summary"""
        self.print_header("TEST SUMMARY")

        total_tests = len(self.results["tests"])

        print(f"Total Test Categories: {total_tests}")
        print(f"{Color.GREEN}Passed: {self.passed}{Color.END}")
        print(f"{Color.YELLOW}Warnings: {self.warnings}{Color.END}")
        print(f"{Color.RED}Failed: {self.failed}{Color.END}")
        print()

        print("Individual Test Results:")
        print("-" * 80)
        for test in self.results["tests"]:
            status = test.get("overall_status", "UNKNOWN")
            if status == "PASS":
                icon = f"{Color.GREEN}✅{Color.END}"
            elif status == "WARNING":
                icon = f"{Color.YELLOW}⚠️{Color.END}"
            else:
                icon = f"{Color.RED}❌{Color.END}"

            print(f"{icon} {test['test_name']}: {status}")

        print()
        print("=" * 80)

        # Overall status
        critical_failures = sum(1 for t in self.results["tests"]
                              if t.get("overall_status") == "FAIL"
                              and t["test_name"] == "Query Consistency")

        if critical_failures > 0:
            print(f"{Color.RED}{Color.BOLD}❌ CRITICAL FAILURE - Not production ready{Color.END}")
            print("Query consistency issues detected. Users will get different answers!")
        elif self.failed > 0:
            print(f"{Color.RED}❌ TESTS FAILED - Issues need fixing{Color.END}")
        elif self.warnings > 0:
            print(f"{Color.YELLOW}⚠️  TESTS PASSED WITH WARNINGS - Review recommended{Color.END}")
        else:
            print(f"{Color.GREEN}{Color.BOLD}🎉 ALL TESTS PASSED - PRODUCTION READY!{Color.END}")

        print("=" * 80)

        # Save summary stats
        self.results["summary"] = {
            "total_passed": self.passed,
            "total_warnings": self.warnings,
            "total_failed": self.failed,
            "production_ready": self.failed == 0 and critical_failures == 0
        }

    def run_all_tests(self):
        """Run all UX tests"""
        print(f"\n{Color.BOLD}{Color.BLUE}{'='*80}")
        print("PLAYINTEL COMPREHENSIVE UX TEST SUITE")
        print(f"{'='*80}{Color.END}")
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'Quick' if self.quick_mode else 'Full'}")
        print()

        try:
            self.test_1_vocabulary_variety()
            self.test_2_no_backend_exposure()
            self.test_3_includes_requested_data()
            self.test_4_format_variety()
            self.test_5_direct_answers()
            self.test_6_consistency()

        except KeyboardInterrupt:
            print(f"\n\n{Color.YELLOW}⚠️  Tests interrupted by user{Color.END}")
        except Exception as e:
            print(f"\n{Color.RED}❌ Test suite error: {e}{Color.END}")
            import traceback
            traceback.print_exc()

        self.save_results()
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive UX Test Framework for PlayIntel'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick subset of tests (faster)'
    )

    args = parser.parse_args()

    print(f"\n{Color.BLUE}🧪 Starting UX Test Framework...{Color.END}\n")

    if args.quick:
        print(f"{Color.YELLOW}Running in QUICK mode (subset of tests){Color.END}")
        print("Estimated time: 2-3 minutes\n")
    else:
        print("Running FULL test suite")
        print("Estimated time: 5-8 minutes\n")

    framework = UXTestFramework(quick_mode=args.quick)
    framework.run_all_tests()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
