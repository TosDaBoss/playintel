#!/usr/bin/env python3
"""
Test UX Fixes - Verify all 4 improvements are working
"""

import requests
import json
import time

API_URL = "http://localhost:8000/api/chat"

def test_vocabulary_variety():
    """Test 1: Check vocabulary variety (no overused words)"""
    print("\n" + "="*80)
    print("TEST 1: Vocabulary Variety")
    print("="*80)

    question = "What are the top 5 FPS games?"
    bad_words = ["honestly", "realistically"]

    responses = []
    for i in range(3):
        try:
            response = requests.post(API_URL, json={
                "question": question,
                "conversation_history": []
            }, timeout=30)

            if response.status_code == 200:
                answer = response.json().get("answer", "").lower()
                responses.append(answer)

                # Check for bad words
                found_bad = []
                for word in bad_words:
                    count = answer.count(word)
                    if count > 0:
                        found_bad.append(f"{word} ({count}x)")

                print(f"\nAttempt {i+1}:")
                if found_bad:
                    print(f"  ⚠️  Found overused words: {', '.join(found_bad)}")
                else:
                    print(f"  ✅ No overused words")

            time.sleep(2)

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Check variety across responses
    if len(responses) == 3:
        unique_responses = len(set(responses))
        print(f"\nVariety: {unique_responses}/3 unique responses")
        if unique_responses >= 2:
            print("✅ Good variety in responses")
        else:
            print("⚠️  Responses too similar")

    return len(responses) == 3 and all(word not in r for r in responses for word in bad_words)


def test_no_backend_exposure():
    """Test 2: No backend exposure"""
    print("\n" + "="*80)
    print("TEST 2: No Backend Exposure")
    print("="*80)

    test_cases = [
        "Show me action games",
        "What's the most popular genre?",
        "Compare CS:GO vs PUBG"
    ]

    backend_phrases = [
        "looking at", "checking", "let me check", "dataset",
        "database", "query", "sql", "analyzing the data"
    ]

    all_clean = True

    for question in test_cases:
        print(f"\nQ: {question}")

        try:
            response = requests.post(API_URL, json={
                "question": question,
                "conversation_history": []
            }, timeout=30)

            if response.status_code == 200:
                answer = response.json().get("answer", "").lower()

                found = []
                for phrase in backend_phrases:
                    if phrase in answer:
                        found.append(phrase)

                if found:
                    print(f"  ❌ Found backend terms: {', '.join(found)}")
                    all_clean = False
                else:
                    print(f"  ✅ Clean - no backend exposure")
            else:
                print(f"  ⚠️  HTTP {response.status_code}")

            time.sleep(2)

        except Exception as e:
            print(f"  ❌ Error: {e}")

    return all_clean


def test_includes_requested_data():
    """Test 3: Always includes requested data"""
    print("\n" + "="*80)
    print("TEST 3: Includes All Requested Data")
    print("="*80)

    test_cases = [
        {
            "question": "Show me games with highest ratings and most owners",
            "required_in_sql": ["rating", "owner"],
            "required_in_data": ["rating", "owner"]
        },
        {
            "question": "What are the top-rated action games?",
            "required_in_sql": ["rating"],
            "required_in_data": ["rating"]
        }
    ]

    all_pass = True

    for case in test_cases:
        print(f"\nQ: {case['question']}")

        try:
            response = requests.post(API_URL, json={
                "question": case["question"],
                "conversation_history": []
            }, timeout=30)

            if response.status_code == 200:
                data = response.json()
                sql = (data.get("sql_query") or "").lower()
                result_data = data.get("data", [])

                # Check SQL
                sql_has_all = all(req in sql for req in case["required_in_sql"])
                print(f"  SQL includes {case['required_in_sql']}: {'✅' if sql_has_all else '❌'}")

                # Check data
                if result_data and len(result_data) > 0:
                    data_keys = str(result_data[0].keys()).lower()
                    data_has_all = all(req in data_keys for req in case["required_in_data"])
                    print(f"  Data includes {case['required_in_data']}: {'✅' if data_has_all else '❌'}")

                    if not sql_has_all or not data_has_all:
                        all_pass = False
                else:
                    print(f"  ⚠️  No data returned")

            time.sleep(2)

        except Exception as e:
            print(f"  ❌ Error: {e}")

    return all_pass


def test_format_variety():
    """Test 4: Response format varies by question type"""
    print("\n" + "="*80)
    print("TEST 4: Response Format Variety")
    print("="*80)

    test_cases = [
        {"q": "What are the top 3 games?", "type": "list"},
        {"q": "Compare Indie vs AAA games", "type": "comparison"},
        {"q": "What genre is trending?", "type": "trend"},
        {"q": "Should I add achievements?", "type": "advice"}
    ]

    formats_used = set()

    for case in test_cases:
        print(f"\nQ: {case['q']}")
        print(f"Expected type: {case['type']}")

        try:
            response = requests.post(API_URL, json={
                "question": case["q"],
                "conversation_history": []
            }, timeout=30)

            if response.status_code == 200:
                answer = response.json().get("answer", "")

                # Heuristic format detection
                has_bullets = "•" in answer or "-" in answer[:100]
                has_numbered = any(f"{i}." in answer for i in range(1, 6))
                has_comparison_words = any(w in answer.lower() for w in ["vs", "compared", "difference"])
                has_advice_words = any(w in answer.lower() for w in ["should", "recommend", "consider"])

                detected_format = "unknown"
                if has_comparison_words:
                    detected_format = "comparison"
                elif has_advice_words:
                    detected_format = "advice"
                elif has_bullets or has_numbered:
                    detected_format = "list"
                else:
                    detected_format = "narrative"

                formats_used.add(detected_format)

                print(f"  Detected format: {detected_format}")
                print(f"  Structure: {'bullets' if has_bullets else 'numbered' if has_numbered else 'paragraph'}")

            time.sleep(2)

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\nTotal format variety: {len(formats_used)} different formats")
    return len(formats_used) >= 2


def main():
    print("="*80)
    print("PlayIntel UX Improvements - Test Suite")
    print("="*80)

    results = {
        "Vocabulary Variety": test_vocabulary_variety(),
        "No Backend Exposure": test_no_backend_exposure(),
        "Includes Requested Data": test_includes_requested_data(),
        "Format Variety": test_format_variety()
    }

    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\nOverall: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All UX improvements working correctly!")
    elif total_passed >= total_tests * 0.75:
        print("\n⚠️  Most improvements working, some issues remain")
    else:
        print("\n❌ Major issues - needs investigation")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
