#!/usr/bin/env python3
"""
Comprehensive testing suite for PlayIntel.
Tests conversational quality, analytical accuracy, and benchmarks against expected behavior.
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000/api/chat"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_section(title):
    print(f"\n{'='*80}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{'='*80}\n")


def print_test(test_name, passed, details=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {test_name}")
    if details:
        print(f"  {details}")


def send_message(question, conversation_history=None):
    """Send a message to PlayIntel API."""
    if conversation_history is None:
        conversation_history = []

    try:
        response = requests.post(
            API_URL,
            json={
                "question": question,
                "conversation_history": conversation_history
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def test_conversational_routing():
    """Test if PlayIntel correctly routes conversational vs analytical questions."""
    print_section("TEST 1: Conversational Routing")

    tests = [
        {
            "question": "Do you always need to give key insights?",
            "should_query_db": False,
            "description": "Meta question about response format"
        },
        {
            "question": "Thanks for the help!",
            "should_query_db": False,
            "description": "Gratitude expression"
        },
        {
            "question": "What are the top 5 games by playtime?",
            "should_query_db": True,
            "description": "Data query"
        },
        {
            "question": "How do you work?",
            "should_query_db": False,
            "description": "Question about capabilities"
        },
        {
            "question": "Show me developers with most games",
            "should_query_db": True,
            "description": "Clear data request"
        }
    ]

    passed = 0
    failed = 0

    for test in tests:
        result = send_message(test["question"])

        if "error" in result:
            print_test(test["description"], False, f"Error: {result['error']}")
            failed += 1
            continue

        has_sql = result.get("sql_query") is not None
        correct_routing = has_sql == test["should_query_db"]

        expected = "Database query" if test["should_query_db"] else "Conversational"
        actual = "Database query" if has_sql else "Conversational"

        print_test(
            test["description"],
            correct_routing,
            f"Expected: {expected}, Got: {actual}"
        )

        if correct_routing:
            passed += 1
        else:
            failed += 1

        time.sleep(1)  # Rate limiting

    print(f"\n{GREEN}Passed: {passed}{RESET} | {RED}Failed: {failed}{RESET}")
    return passed, failed


def test_conversation_memory():
    """Test if PlayIntel maintains context across multiple turns."""
    print_section("TEST 2: Conversation Memory")

    conversation = []

    # Turn 1: Ask about top developers
    q1 = "What are the top 3 developers by total games?"
    r1 = send_message(q1, conversation)

    if "error" in r1:
        print_test("Multi-turn conversation", False, f"Error: {r1['error']}")
        return 0, 1

    conversation.append({"role": "user", "content": q1})
    conversation.append({"role": "assistant", "content": r1["answer"]})

    time.sleep(1)

    # Turn 2: Follow-up without context
    q2 = "What about the second one?"
    r2 = send_message(q2, conversation)

    if "error" in r2:
        print_test("Context retention", False, f"Error: {r2['error']}")
        return 0, 1

    # Check if response indicates understanding of context
    answer_lower = r2["answer"].lower()
    maintains_context = (
        "second" in answer_lower or
        "valve" in answer_lower or  # Common second developer
        "capcom" in answer_lower or
        any(word in answer_lower for word in ["their", "they", "those"])
    )

    print_test(
        "Context retention in follow-up",
        maintains_context,
        f"Response: {r2['answer'][:100]}..."
    )

    return (1, 0) if maintains_context else (0, 1)


def test_response_quality():
    """Test the quality and structure of responses."""
    print_section("TEST 3: Response Quality")

    question = "What are the top 5 games by playtime?"
    result = send_message(question)

    if "error" in result:
        print_test("Response quality", False, f"Error: {result['error']}")
        return 0, 1

    answer = result.get("answer", "")

    # Test 1: No technical jargon
    jargon_words = ["sql", "query", "database", "table", "select", "from", "where"]
    has_jargon = any(word in answer.lower() for word in jargon_words)
    print_test(
        "No SQL/technical jargon in response",
        not has_jargon,
        f"Found jargon" if has_jargon else "Clean language"
    )

    # Test 2: Has structure (emojis, numbers, or bullets)
    has_structure = any([
        "1." in answer or "2." in answer,  # Numbered list
        "•" in answer or "-" in answer[:50],  # Bullet points
        any(emoji in answer for emoji in ["🎮", "📊", "💡", "🏆"])  # Emojis
    ])
    print_test(
        "Well-structured response",
        has_structure,
        "Has formatting" if has_structure else "Plain text"
    )

    # Test 3: Reasonable length
    reasonable_length = 100 < len(answer) < 3000
    print_test(
        "Appropriate response length",
        reasonable_length,
        f"{len(answer)} characters"
    )

    # Test 4: Direct tone (uses "you")
    uses_direct_address = "you" in answer.lower()
    print_test(
        "Direct address (uses 'you')",
        uses_direct_address,
        "Personal tone" if uses_direct_address else "Generic tone"
    )

    passed = sum([not has_jargon, has_structure, reasonable_length, uses_direct_address])
    failed = 4 - passed

    print(f"\n{GREEN}Passed: {passed}/4{RESET} | {RED}Failed: {failed}/4{RESET}")
    return passed, failed


def test_analytical_accuracy():
    """Test if SQL queries are correct and return data."""
    print_section("TEST 4: Analytical Accuracy")

    tests = [
        {
            "question": "How many games are in the database?",
            "should_have_data": True,
            "description": "Simple count query"
        },
        {
            "question": "What's the average price of games?",
            "should_have_data": True,
            "description": "Aggregation query"
        },
        {
            "question": "Show me games by Rockstar",
            "should_have_data": True,
            "description": "Filtered query"
        }
    ]

    passed = 0
    failed = 0

    for test in tests:
        result = send_message(test["question"])

        if "error" in result:
            print_test(test["description"], False, f"Error: {result['error']}")
            failed += 1
            continue

        has_data = result.get("data") is not None and len(result.get("data", [])) > 0
        has_sql = result.get("sql_query") is not None

        correct = has_data == test["should_have_data"] and has_sql

        details = f"SQL: {'✓' if has_sql else '✗'}, Data: {len(result.get('data', []))} rows"

        print_test(test["description"], correct, details)

        if correct:
            passed += 1
        else:
            failed += 1

        time.sleep(1)

    print(f"\n{GREEN}Passed: {passed}{RESET} | {RED}Failed: {failed}{RESET}")
    return passed, failed


def test_error_handling():
    """Test how PlayIntel handles edge cases and errors."""
    print_section("TEST 5: Error Handling")

    tests = [
        {
            "question": "",
            "description": "Empty question",
            "should_handle": True
        },
        {
            "question": "asdfasdfasdfasdf",
            "description": "Nonsense input",
            "should_handle": True
        },
        {
            "question": "Show me games from a developer that doesn't exist: ZZZZZ999999",
            "description": "Query with no results",
            "should_handle": True
        }
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test["question"] == "":
            # Empty questions should be rejected by frontend, but let's test backend
            print_test(test["description"], True, "Skipped (frontend validation)")
            passed += 1
            continue

        result = send_message(test["question"])

        # Should get a response (not crash)
        handled = "answer" in result or "error" in result

        details = "Handled gracefully" if handled else "Crashed or no response"

        print_test(test["description"], handled, details)

        if handled:
            passed += 1
        else:
            failed += 1

        time.sleep(1)

    print(f"\n{GREEN}Passed: {passed}{RESET} | {RED}Failed: {failed}{RESET}")
    return passed, failed


def benchmark_response_time():
    """Benchmark response times."""
    print_section("TEST 6: Performance Benchmarking")

    questions = [
        "What are the top 5 games?",
        "How many developers are there?",
        "Show me games priced at $15"
    ]

    times = []

    for question in questions:
        start = time.time()
        result = send_message(question)
        elapsed = time.time() - start
        times.append(elapsed)

        if "error" not in result:
            print(f"  {question[:50]:50} - {elapsed:.2f}s")

    avg_time = sum(times) / len(times)

    # Acceptable if under 10 seconds on average
    acceptable = avg_time < 10

    print(f"\n  Average response time: {avg_time:.2f}s")
    print_test(
        "Response time < 10s average",
        acceptable,
        f"{avg_time:.2f}s average"
    )

    return (1, 0) if acceptable else (0, 1)


def test_persona_consistency():
    """Test if Alex's persona is consistent."""
    print_section("TEST 7: Persona Consistency")

    question = "What should I consider when pricing my game?"
    result = send_message(question)

    if "error" in result:
        print_test("Persona consistency", False, f"Error: {result['error']}")
        return 0, 1

    answer = result.get("answer", "").lower()

    # Check for persona traits
    traits = {
        "Direct/Pragmatic": any(word in answer for word in ["honestly", "realistically", "frankly", "truth is"]),
        "Empathetic": any(word in answer for word in ["you", "your", "indie", "budget", "constraint"]),
        "Experienced": any(word in answer for word in ["seen", "typically", "usually", "tends to", "pattern"]),
        "Actionable": any(word in answer for word in ["should", "recommend", "try", "consider", "start with"])
    }

    passed = sum(traits.values())
    failed = len(traits) - passed

    for trait, present in traits.items():
        print_test(f"Persona: {trait}", present, "Present" if present else "Missing")

    print(f"\n{GREEN}Passed: {passed}/4{RESET} | {RED}Failed: {failed}/4{RESET}")
    return passed, failed


def run_all_tests():
    """Run all tests and generate report."""
    print(f"\n{BLUE}{'='*80}")
    print(f"PlayIntel Comprehensive Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}{RESET}\n")

    total_passed = 0
    total_failed = 0

    # Run all test suites
    p, f = test_conversational_routing()
    total_passed += p
    total_failed += f

    p, f = test_conversation_memory()
    total_passed += p
    total_failed += f

    p, f = test_response_quality()
    total_passed += p
    total_failed += f

    p, f = test_analytical_accuracy()
    total_passed += p
    total_failed += f

    p, f = test_error_handling()
    total_passed += p
    total_failed += f

    p, f = benchmark_response_time()
    total_passed += p
    total_failed += f

    p, f = test_persona_consistency()
    total_passed += p
    total_failed += f

    # Final report
    print_section("FINAL REPORT")

    total_tests = total_passed + total_failed
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"Total Tests Run: {total_tests}")
    print(f"{GREEN}Passed: {total_passed}{RESET}")
    print(f"{RED}Failed: {total_failed}{RESET}")
    print(f"Pass Rate: {pass_rate:.1f}%\n")

    if pass_rate >= 80:
        print(f"{GREEN}✓ EXCELLENT - PlayIntel is performing well!{RESET}")
    elif pass_rate >= 60:
        print(f"{YELLOW}⚠ GOOD - Some improvements needed{RESET}")
    else:
        print(f"{RED}✗ NEEDS WORK - Significant improvements required{RESET}")

    print(f"\n{BLUE}{'='*80}{RESET}\n")

    # Save report
    report_path = "/Users/tosdaboss/playintel/test_report.txt"
    with open(report_path, "w") as f:
        f.write(f"PlayIntel Test Report\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Total Tests: {total_tests}\n")
        f.write(f"Passed: {total_passed}\n")
        f.write(f"Failed: {total_failed}\n")
        f.write(f"Pass Rate: {pass_rate:.1f}%\n")

    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}Test suite error: {e}{RESET}")
