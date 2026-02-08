#!/usr/bin/env python3
"""
PlayIntel Production Readiness Test Suite

Tests for:
1. Response consistency vs randomness
2. Context relevance
3. Backend exposure (should not reveal technical details)
4. Long conversation coherence (20+ messages)
"""

import requests
import json
import time
from typing import List, Dict
from datetime import datetime


API_URL = "http://localhost:8000/api/chat"
TEST_RESULTS_FILE = "/Users/tosdaboss/playintel/test_results.json"


class ProductionReadinessTest:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }

    def test_response_consistency(self):
        """
        Test 1: Response Randomness vs Consistency
        Ask the same question 3 times and check if responses are too similar or too different
        """
        print("\n" + "="*80)
        print("TEST 1: Response Consistency vs Randomness")
        print("="*80)

        test_questions = [
            "What are the top 5 FPS games?",
            "Show me successful indie games",
            "What games have the best value?"
        ]

        test_result = {
            "test_name": "Response Consistency",
            "status": "PASS",
            "details": []
        }

        for question in test_questions:
            print(f"\nTesting question: '{question}'")
            responses = []

            for i in range(3):
                try:
                    response = requests.post(API_URL, json={
                        "question": question,
                        "conversation_history": []
                    }, timeout=20)

                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get('answer', '')
                        sql = data.get('sql_query', '')
                        responses.append({
                            "attempt": i + 1,
                            "answer": answer,
                            "sql": sql,
                            "answer_length": len(answer)
                        })
                        print(f"  Attempt {i+1}: {len(answer)} chars, SQL: {sql[:60]}...")
                    else:
                        print(f"  ❌ Attempt {i+1} failed: HTTP {response.status_code}")
                        test_result["status"] = "FAIL"

                    time.sleep(2)  # Avoid rate limiting

                except Exception as e:
                    print(f"  ❌ Attempt {i+1} error: {e}")
                    test_result["status"] = "FAIL"

            # Analyze consistency
            if len(responses) == 3:
                # Check SQL consistency (should be same or very similar)
                sqls = [r['sql'] for r in responses]
                sql_same = len(set(sqls)) == 1

                # Check answer variety (should have some variation in wording)
                answers = [r['answer'] for r in responses]
                answer_lengths = [len(a) for a in answers]
                avg_length = sum(answer_lengths) / len(answer_lengths)
                length_variance = sum(abs(l - avg_length) for l in answer_lengths) / len(answer_lengths)

                # Answers should be similar but not identical
                answers_identical = len(set(answers)) == 1

                detail = {
                    "question": question,
                    "sql_consistent": sql_same,
                    "answers_identical": answers_identical,
                    "avg_answer_length": int(avg_length),
                    "length_variance": int(length_variance),
                    "verdict": "GOOD" if sql_same and not answers_identical else "NEEDS REVIEW"
                }

                print(f"\n  Analysis:")
                print(f"    SQL Consistent: {sql_same} ({'✅' if sql_same else '⚠️'})")
                print(f"    Answers Identical: {answers_identical} ({'⚠️' if answers_identical else '✅'})")
                print(f"    Avg Length: {int(avg_length)} chars, Variance: {int(length_variance)}")
                print(f"    Verdict: {detail['verdict']}")

                if answers_identical:
                    print("    ⚠️  Warning: Responses are identical. Consider adding more variety.")
                    test_result["status"] = "WARNING"

                test_result["details"].append(detail)

        self.results["tests"].append(test_result)
        print(f"\n{'='*80}")
        print(f"Test 1 Result: {test_result['status']}")
        print(f"{'='*80}")

    def test_context_relevance(self):
        """
        Test 2: Context Relevance
        Ask questions and verify responses actually answer what was asked
        """
        print("\n" + "="*80)
        print("TEST 2: Context Relevance")
        print("="*80)

        test_cases = [
            {
                "question": "What are the top 3 FPS games?",
                "expected_keywords": ["fps", "shooter", "counter-strike", "pubg", "first-person"],
                "must_not_contain": ["rpg", "puzzle", "strategy"]
            },
            {
                "question": "Show me free to play games",
                "expected_keywords": ["free", "f2p", "$0"],
                "must_not_contain": ["paid", "$60", "premium"]
            },
            {
                "question": "Which games have the best reviews?",
                "expected_keywords": ["rating", "review", "positive", "%", "score"],
                "must_not_contain": ["worst", "negative rating"]
            },
            {
                "question": "What games support Linux?",
                "expected_keywords": ["linux", "platform"],
                "must_not_contain": ["windows only", "mac only"]
            }
        ]

        test_result = {
            "test_name": "Context Relevance",
            "status": "PASS",
            "details": []
        }

        for case in test_cases:
            print(f"\nQuestion: '{case['question']}'")

            try:
                response = requests.post(API_URL, json={
                    "question": case["question"],
                    "conversation_history": []
                }, timeout=20)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '').lower()

                    # Check for expected keywords
                    found_keywords = [kw for kw in case["expected_keywords"] if kw.lower() in answer]
                    missing_keywords = [kw for kw in case["expected_keywords"] if kw.lower() not in answer]

                    # Check for unwanted content
                    found_unwanted = [kw for kw in case["must_not_contain"] if kw.lower() in answer]

                    # Determine if relevant
                    relevance_score = len(found_keywords) / len(case["expected_keywords"]) * 100
                    is_relevant = relevance_score >= 30 and len(found_unwanted) == 0

                    detail = {
                        "question": case["question"],
                        "relevance_score": round(relevance_score, 1),
                        "found_keywords": found_keywords,
                        "missing_keywords": missing_keywords,
                        "unwanted_found": found_unwanted,
                        "verdict": "RELEVANT" if is_relevant else "NOT RELEVANT"
                    }

                    print(f"  Relevance Score: {relevance_score:.1f}%")
                    print(f"  Found Keywords: {found_keywords}")
                    if missing_keywords:
                        print(f"  Missing Keywords: {missing_keywords}")
                    if found_unwanted:
                        print(f"  ⚠️  Unwanted Content: {found_unwanted}")
                        test_result["status"] = "FAIL"

                    print(f"  Verdict: {detail['verdict']} {'✅' if is_relevant else '❌'}")

                    if not is_relevant:
                        test_result["status"] = "FAIL"

                    test_result["details"].append(detail)

                else:
                    print(f"  ❌ Request failed: HTTP {response.status_code}")
                    test_result["status"] = "FAIL"

            except Exception as e:
                print(f"  ❌ Error: {e}")
                test_result["status"] = "FAIL"

            time.sleep(2)

        self.results["tests"].append(test_result)
        print(f"\n{'='*80}")
        print(f"Test 2 Result: {test_result['status']}")
        print(f"{'='*80}")

    def test_backend_exposure(self):
        """
        Test 3: Backend Exposure
        Verify responses don't reveal technical implementation details
        """
        print("\n" + "="*80)
        print("TEST 3: Backend Exposure (Technical Details Leakage)")
        print("="*80)

        # Technical terms that should NOT appear in user-facing responses
        forbidden_terms = [
            "fact_game_metrics",  # Table name
            "dim_developers",      # Table name
            "psycopg",            # Database driver
            "postgresql",         # Database system
            "sql error",          # Error message
            "query failed",       # Error message
            "connection error",   # Error message
            "cursor",             # Database term
            "fetchall",           # Database term
            "SELECT * FROM",      # Raw SQL in answer
            "WHERE",              # Raw SQL keywords (some context is ok)
            "JOIN",               # Raw SQL keywords
            "anthropic",          # AI provider
            "claude",             # AI model (unless user asks about it)
            "system prompt",      # Implementation detail
            "knowledge base",     # Implementation detail
            "alex_knowledge",     # File name
        ]

        test_questions = [
            "What are the top games?",
            "Show me FPS games",
            "Which developers make the best games?",
            "What's the most popular genre?",
            "Tell me about free games"
        ]

        test_result = {
            "test_name": "Backend Exposure",
            "status": "PASS",
            "details": []
        }

        for question in test_questions:
            print(f"\nQuestion: '{question}'")

            try:
                response = requests.post(API_URL, json={
                    "question": question,
                    "conversation_history": []
                }, timeout=20)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '').lower()

                    # Check for forbidden terms
                    found_forbidden = [term for term in forbidden_terms if term.lower() in answer]

                    # SQL query should be in the response data but NOT in the answer text
                    sql_in_answer = "select" in answer and "from" in answer

                    detail = {
                        "question": question,
                        "forbidden_terms_found": found_forbidden,
                        "sql_in_answer": sql_in_answer,
                        "verdict": "CLEAN" if not found_forbidden and not sql_in_answer else "EXPOSED"
                    }

                    if found_forbidden or sql_in_answer:
                        print(f"  ❌ Backend Exposure Detected!")
                        if found_forbidden:
                            print(f"     Forbidden terms: {found_forbidden}")
                        if sql_in_answer:
                            print(f"     Raw SQL found in answer text")
                        test_result["status"] = "FAIL"
                    else:
                        print(f"  ✅ Clean - No technical details exposed")

                    test_result["details"].append(detail)

                else:
                    print(f"  ⚠️  Request failed: HTTP {response.status_code}")

            except Exception as e:
                print(f"  ❌ Error: {e}")
                test_result["status"] = "FAIL"

            time.sleep(2)

        self.results["tests"].append(test_result)
        print(f"\n{'='*80}")
        print(f"Test 3 Result: {test_result['status']}")
        print(f"{'='*80}")

    def test_long_conversation(self):
        """
        Test 4: Long Conversation Coherence
        Maintain context over 20+ back-and-forth messages
        """
        print("\n" + "="*80)
        print("TEST 4: Long Conversation Coherence (20+ Messages)")
        print("="*80)

        conversation_flow = [
            {"user": "What are the top 3 FPS games?", "expect_context": []},
            {"user": "Tell me more about the first one", "expect_context": ["counter-strike", "cs:go", "first"]},
            {"user": "What's its player count?", "expect_context": ["player", "owner", "million"]},
            {"user": "How does that compare to PUBG?", "expect_context": ["pubg", "compare", "150"]},
            {"user": "What genre is PUBG?", "expect_context": ["battle royale", "shooter", "action"]},
            {"user": "Show me other battle royale games", "expect_context": ["apex", "fortnite", "battle"]},
            {"user": "Which one is free to play?", "expect_context": ["free", "apex", "f2p"]},
            {"user": "What's Apex's rating?", "expect_context": ["apex", "rating", "positive", "%"]},
            {"user": "Compare it to the first game we discussed", "expect_context": ["counter-strike", "compare", "cs"]},
            {"user": "What platform does that run on?", "expect_context": ["windows", "platform", "mac", "linux"]},
            {"user": "Show me Windows-only shooters", "expect_context": ["windows", "shooter", "fps"]},
            {"user": "Which has the most DLC?", "expect_context": ["dlc", "most", "count"]},
            {"user": "Is that a good sign?", "expect_context": ["dlc", "good", "monetization", "support"]},
            {"user": "What about the game with the least DLC from that list?", "expect_context": ["dlc", "least", "fewest"]},
            {"user": "How many languages does it support?", "expect_context": ["language", "support", "localization"]},
            {"user": "Compare that to the average", "expect_context": ["average", "language", "compare"]},
            {"user": "What's considered good language support?", "expect_context": ["language", "good", "10", "international"]},
            {"user": "Which games from our earlier discussion have that?", "expect_context": ["language", "10", "fps", "earlier"]},
            {"user": "Rank them by player count", "expect_context": ["rank", "player", "owner", "count"]},
            {"user": "What's your overall recommendation from this list?", "expect_context": ["recommend", "best", "fps", "overall"]},
        ]

        conversation_history = []
        test_result = {
            "test_name": "Long Conversation",
            "status": "PASS",
            "details": [],
            "context_maintained": 0,
            "context_lost": 0
        }

        print(f"\nStarting {len(conversation_flow)}-message conversation...\n")

        for i, turn in enumerate(conversation_flow, 1):
            question = turn["user"]
            print(f"[{i}/{len(conversation_flow)}] User: {question}")

            try:
                response = requests.post(API_URL, json={
                    "question": question,
                    "conversation_history": conversation_history
                }, timeout=20)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '')

                    # Add to conversation history
                    conversation_history.append({"role": "user", "content": question})
                    conversation_history.append({"role": "assistant", "content": answer})

                    # Check if context is maintained
                    answer_lower = answer.lower()
                    context_found = any(ctx.lower() in answer_lower for ctx in turn["expect_context"]) if turn["expect_context"] else True

                    detail = {
                        "turn": i,
                        "question": question,
                        "expected_context": turn["expect_context"],
                        "context_maintained": context_found,
                        "answer_preview": answer[:150] + "..."
                    }

                    if context_found or not turn["expect_context"]:
                        print(f"     ✅ Context maintained")
                        test_result["context_maintained"] += 1
                    else:
                        print(f"     ❌ Context lost - Expected: {turn['expect_context']}")
                        test_result["context_lost"] += 1
                        test_result["status"] = "WARNING"

                    test_result["details"].append(detail)

                else:
                    print(f"     ❌ Request failed: HTTP {response.status_code}")
                    test_result["status"] = "FAIL"
                    break

            except Exception as e:
                print(f"     ❌ Error: {e}")
                test_result["status"] = "FAIL"
                break

            time.sleep(2)

        # Calculate context retention rate
        total_turns = len(conversation_flow)
        retention_rate = (test_result["context_maintained"] / total_turns) * 100

        test_result["context_retention_rate"] = round(retention_rate, 1)

        print(f"\n{'='*80}")
        print(f"Long Conversation Results:")
        print(f"  Context Maintained: {test_result['context_maintained']}/{total_turns}")
        print(f"  Context Lost: {test_result['context_lost']}/{total_turns}")
        print(f"  Retention Rate: {retention_rate:.1f}%")

        if retention_rate >= 80:
            print(f"  ✅ Excellent context retention")
        elif retention_rate >= 60:
            print(f"  ⚠️  Acceptable context retention")
            test_result["status"] = "WARNING"
        else:
            print(f"  ❌ Poor context retention")
            test_result["status"] = "FAIL"

        self.results["tests"].append(test_result)
        print(f"\n{'='*80}")
        print(f"Test 4 Result: {test_result['status']}")
        print(f"{'='*80}")

    def save_results(self):
        """Save test results to JSON file"""
        with open(TEST_RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ Test results saved to: {TEST_RESULTS_FILE}")

    def print_summary(self):
        """Print overall test summary"""
        print("\n" + "="*80)
        print("PRODUCTION READINESS SUMMARY")
        print("="*80)

        total_tests = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"] if t["status"] == "PASS")
        warnings = sum(1 for t in self.results["tests"] if t["status"] == "WARNING")
        failed = sum(1 for t in self.results["tests"] if t["status"] == "FAIL")

        print(f"\nTests Run: {total_tests}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ⚠️  Warnings: {warnings}")
        print(f"  ❌ Failed: {failed}")
        print()

        for test in self.results["tests"]:
            status_icon = "✅" if test["status"] == "PASS" else "⚠️" if test["status"] == "WARNING" else "❌"
            print(f"{status_icon} {test['test_name']}: {test['status']}")

        print()
        print("="*80)

        if failed == 0 and warnings == 0:
            print("🎉 ALL TESTS PASSED - READY FOR PRODUCTION!")
        elif failed == 0:
            print("⚠️  TESTS PASSED WITH WARNINGS - Review before production")
        else:
            print("❌ TESTS FAILED - Fix issues before production deployment")

        print("="*80)
        print()

    def run_all_tests(self):
        """Run all production readiness tests"""
        print("="*80)
        print("PLAYINTEL PRODUCTION READINESS TEST SUITE")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            self.test_response_consistency()
            self.test_context_relevance()
            self.test_backend_exposure()
            self.test_long_conversation()
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
        except Exception as e:
            print(f"\n❌ Test suite error: {e}")
            import traceback
            traceback.print_exc()

        self.save_results()
        self.print_summary()


if __name__ == "__main__":
    print("\n🧪 Starting Production Readiness Tests...\n")
    print("This will take approximately 10-15 minutes to complete.")
    print("Tests include:")
    print("  1. Response Consistency vs Randomness")
    print("  2. Context Relevance")
    print("  3. Backend Exposure Detection")
    print("  4. Long Conversation Coherence (20+ messages)")
    print()

    input("Press Enter to begin testing...")

    tester = ProductionReadinessTest()
    tester.run_all_tests()
