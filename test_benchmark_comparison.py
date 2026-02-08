#!/usr/bin/env python3
"""
Benchmark Comparison Test Framework
Compare PlayIntel vs Claude vs ChatGPT

Tests for:
1. Factual accuracy
2. Response consistency (trust)
3. Relevance to question
4. Professional tone
5. Data completeness
6. Clarity and conciseness

Usage:
  python3 test_benchmark_comparison.py
  python3 test_benchmark_comparison.py --playintel-only  (skip Claude/ChatGPT)
"""

import requests
import json
import time
import argparse
import os
from typing import Dict, List, Tuple
from datetime import datetime

# Optional imports (only if API keys are available)
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    import openai
except ImportError:
    openai = None

# Configuration
PLAYINTEL_API = "http://localhost:8000/api/chat"
RESULTS_FILE = "/Users/tosdaboss/playintel/benchmark_results.json"

# API Keys (from environment)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class BenchmarkTest:
    def __init__(self, skip_external=False):
        self.skip_external = skip_external
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_scenarios": [],
            "scoring": {}
        }

        # Initialize clients
        self.anthropic_client = None
        self.openai_available = False

        if not skip_external:
            if ANTHROPIC_API_KEY and Anthropic:
                self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
            if OPENAI_API_KEY and openai:
                openai.api_key = OPENAI_API_KEY
                self.openai_available = True

    def print_header(self, text):
        print(f"\n{Color.BOLD}{'='*80}")
        print(f"{text}")
        print(f"{'='*80}{Color.END}\n")

    def call_playintel(self, question: str) -> Dict:
        """Call PlayIntel API"""
        try:
            response = requests.post(
                PLAYINTEL_API,
                json={"question": question, "conversation_history": []},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "answer": data.get("answer", ""),
                    "data": data.get("data"),
                    "sql": data.get("sql_query"),
                    "error": None
                }
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"error": str(e)}

    def call_claude(self, question: str) -> Dict:
        """Call Claude API directly"""
        if not self.anthropic_client:
            return {"error": "Claude API key not configured"}

        try:
            # Give Claude same context about Steam data
            system_prompt = """You are a Steam market analyst with access to data on 77,000+ games.
You can answer questions about Steam games, playtime, ratings, pricing, etc.
Be direct, factual, and helpful. Don't make up data - if you don't know, say so."""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": question}]
            )

            return {
                "answer": response.content[0].text,
                "data": None,
                "error": None
            }

        except Exception as e:
            return {"error": str(e)}

    def call_chatgpt(self, question: str) -> Dict:
        """Call ChatGPT API"""
        if not self.openai_available:
            return {"error": "OpenAI API key not configured"}

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Steam market analyst with access to data on 77,000+ games. Be direct, factual, and helpful."
                    },
                    {"role": "user", "content": question}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            return {
                "answer": response.choices[0].message.content,
                "data": None,
                "error": None
            }

        except Exception as e:
            return {"error": str(e)}

    def evaluate_factual_accuracy(self, answer: str, expected_facts: List[str]) -> Tuple[int, str]:
        """
        Evaluate if answer contains expected facts
        Returns: (score 0-10, explanation)
        """
        answer_lower = answer.lower()

        facts_found = 0
        for fact in expected_facts:
            if fact.lower() in answer_lower:
                facts_found += 1

        score = int((facts_found / len(expected_facts)) * 10)

        if score >= 8:
            explanation = f"Contains {facts_found}/{len(expected_facts)} expected facts"
        elif score >= 5:
            explanation = f"Partially accurate ({facts_found}/{len(expected_facts)} facts)"
        else:
            explanation = f"Missing key facts ({facts_found}/{len(expected_facts)})"

        return score, explanation

    def evaluate_consistency(self, answer: str, avoid_phrases: List[str]) -> Tuple[int, str]:
        """
        Evaluate consistency indicators (trust factors)
        Returns: (score 0-10, explanation)
        """
        answer_lower = answer.lower()

        issues = []

        # Check for hedging/uncertainty
        uncertainty_words = ["maybe", "probably", "might be", "could be", "i think", "perhaps"]
        uncertainty_count = sum(1 for word in uncertainty_words if word in answer_lower)

        if uncertainty_count > 2:
            issues.append(f"Too much uncertainty ({uncertainty_count} hedging words)")

        # Check for contradictions
        contradictions = ["but", "however", "although", "on the other hand"]
        contradiction_count = sum(1 for word in contradictions if word in answer_lower)

        if contradiction_count > 3:
            issues.append(f"Too many contradictions ({contradiction_count})")

        # Check for phrases to avoid
        for phrase in avoid_phrases:
            if phrase.lower() in answer_lower:
                issues.append(f"Contains '{phrase}'")

        # Calculate score
        score = 10 - (len(issues) * 2)
        score = max(0, min(10, score))

        explanation = "Consistent and clear" if score >= 8 else f"Issues: {', '.join(issues)}"

        return score, explanation

    def evaluate_relevance(self, question: str, answer: str) -> Tuple[int, str]:
        """
        Evaluate if answer directly addresses the question
        Returns: (score 0-10, explanation)
        """
        answer_lower = answer.lower()
        question_lower = question.lower()

        # Extract key terms from question
        key_terms = []

        if "average" in question_lower or "typical" in question_lower:
            key_terms.append("average")

        if "$" in question or "dollar" in question_lower or "price" in question_lower:
            key_terms.append("price")

        if "playtime" in question_lower or "hours" in question_lower:
            key_terms.append("hours")

        if "rating" in question_lower or "review" in question_lower:
            key_terms.append("rating")

        if "fps" in question_lower or "action" in question_lower or "genre" in question_lower:
            key_terms.append("genre/type")

        # Check if answer contains these terms
        terms_found = 0
        for term in key_terms:
            # Special handling for genre/type - check for actual genre names or game types
            if term == "genre/type":
                # Look for genre mentions: fps, action, rpg, strategy, or generic "game" mentions
                genre_indicators = ["fps", "first-person", "action", "rpg", "strategy", "shooter", "game", "genre", "type"]
                if any(indicator in answer_lower for indicator in genre_indicators):
                    terms_found += 1
            elif term in answer_lower or any(syn in answer_lower for syn in [term + "s", term + "d"]):
                terms_found += 1

        # Check if answer is too long (rambling)
        word_count = len(answer.split())
        too_long = word_count > 300

        # Calculate score
        if len(key_terms) > 0:
            relevance_score = (terms_found / len(key_terms)) * 10
        else:
            relevance_score = 8  # Default if no key terms

        if too_long:
            relevance_score -= 2

        score = max(0, min(10, int(relevance_score)))

        if score >= 8:
            explanation = f"Directly addresses question ({terms_found}/{len(key_terms)} key terms)"
        elif score >= 5:
            explanation = f"Partially relevant ({terms_found}/{len(key_terms)} key terms)"
        else:
            explanation = "Off-topic or too vague"

        if too_long:
            explanation += f" (verbose: {word_count} words)"

        return score, explanation

    def evaluate_professionalism(self, answer: str) -> Tuple[int, str]:
        """
        Evaluate professional tone (builds trust)
        Returns: (score 0-10, explanation)
        """
        answer_lower = answer.lower()

        issues = []

        # Check for unprofessional elements
        if answer.count("!") > 3:
            issues.append("Too many exclamations")

        if "lol" in answer_lower or "haha" in answer_lower:
            issues.append("Unprofessional language")

        # Check for overly casual
        very_casual = ["yeah", "nah", "gonna", "wanna", "kinda", "sorta"]
        casual_count = sum(1 for word in very_casual if word in answer_lower)

        if casual_count > 2:
            issues.append(f"Too casual ({casual_count} casual words)")

        # Check for appropriate formality
        has_structure = "•" in answer or "-" in answer or any(str(i)+"." in answer for i in range(1, 6))

        # Calculate score
        score = 10 - (len(issues) * 3)
        if has_structure:
            score += 1

        score = max(0, min(10, score))

        if score >= 8:
            explanation = "Professional and clear"
        else:
            explanation = f"Issues: {', '.join(issues)}"

        return score, explanation

    def evaluate_data_completeness(self, answer: str, question: str, has_data: bool) -> Tuple[int, str]:
        """
        Evaluate if response provides complete data
        Returns: (score 0-10, explanation)
        """
        # Questions that should have specific data
        data_questions = [
            "average", "how many", "what is", "show me", "list", "top"
        ]

        needs_data = any(phrase in question.lower() for phrase in data_questions)

        if not needs_data:
            return 10, "Question doesn't require specific data"

        # Check if answer contains numbers
        import re
        numbers = re.findall(r'\d+\.?\d*', answer)

        has_numbers = len(numbers) > 0

        if has_data:  # PlayIntel with actual database access
            if has_numbers:
                score = 10
                explanation = "Provides specific data from database"
            else:
                score = 5
                explanation = "Has database access but didn't provide numbers"
        else:  # Claude/ChatGPT without database
            if has_numbers:
                score = 6
                explanation = "Provides numbers but no database verification"
            else:
                score = 3
                explanation = "No specific data provided"

        return score, explanation

    def evaluate_clarity(self, answer: str) -> Tuple[int, str]:
        """
        Evaluate clarity and conciseness
        Returns: (score 0-10, explanation)
        """
        word_count = len(answer.split())
        sentence_count = answer.count(".") + answer.count("!") + answer.count("?")

        avg_sentence_length = word_count / max(sentence_count, 1)

        issues = []

        # Too long = hard to read
        if word_count > 250:
            issues.append("Too verbose")

        # Too short = not enough info
        if word_count < 20:
            issues.append("Too brief")

        # Sentences too long = hard to parse
        if avg_sentence_length > 30:
            issues.append("Sentences too long")

        # Check for structure
        has_structure = "•" in answer or "\n" in answer or any(str(i)+"." in answer for i in range(1, 6))

        # Calculate score
        score = 10 - (len(issues) * 2)
        if has_structure and word_count >= 50:
            score += 1

        score = max(0, min(10, score))

        if score >= 8:
            explanation = f"Clear and concise ({word_count} words)"
        else:
            explanation = f"{', '.join(issues)} ({word_count} words)"

        return score, explanation

    def run_scenario(self, scenario: Dict):
        """Run a single test scenario across all systems"""
        question = scenario["question"]
        expected_facts = scenario.get("expected_facts", [])
        avoid_phrases = scenario.get("avoid_phrases", [])

        print(f"\n{Color.BLUE}{Color.BOLD}Scenario: {scenario['name']}{Color.END}")
        print(f"Question: {question}")
        print("-" * 80)

        results = {
            "name": scenario["name"],
            "question": question,
            "systems": {}
        }

        # Test PlayIntel
        print(f"\n{Color.BOLD}Testing PlayIntel...{Color.END}")
        playintel_response = self.call_playintel(question)

        if playintel_response.get("error"):
            print(f"{Color.RED}❌ Error: {playintel_response['error']}{Color.END}")
            results["systems"]["PlayIntel"] = {"error": playintel_response["error"]}
        else:
            answer = playintel_response["answer"]
            has_data = playintel_response["data"] is not None

            # Evaluate
            fact_score, fact_exp = self.evaluate_factual_accuracy(answer, expected_facts)
            cons_score, cons_exp = self.evaluate_consistency(answer, avoid_phrases)
            rel_score, rel_exp = self.evaluate_relevance(question, answer)
            prof_score, prof_exp = self.evaluate_professionalism(answer)
            data_score, data_exp = self.evaluate_data_completeness(answer, question, has_data)
            clar_score, clar_exp = self.evaluate_clarity(answer)

            total_score = fact_score + cons_score + rel_score + prof_score + data_score + clar_score

            results["systems"]["PlayIntel"] = {
                "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                "full_answer": answer,
                "has_database_access": has_data,
                "scores": {
                    "factual_accuracy": {"score": fact_score, "explanation": fact_exp},
                    "consistency": {"score": cons_score, "explanation": cons_exp},
                    "relevance": {"score": rel_score, "explanation": rel_exp},
                    "professionalism": {"score": prof_score, "explanation": prof_exp},
                    "data_completeness": {"score": data_score, "explanation": data_exp},
                    "clarity": {"score": clar_score, "explanation": clar_exp},
                    "total": total_score
                }
            }

            print(f"  Factual Accuracy: {fact_score}/10 - {fact_exp}")
            print(f"  Consistency: {cons_score}/10 - {cons_exp}")
            print(f"  Relevance: {rel_score}/10 - {rel_exp}")
            print(f"  Professionalism: {prof_score}/10 - {prof_exp}")
            print(f"  Data Completeness: {data_score}/10 - {data_exp}")
            print(f"  Clarity: {clar_score}/10 - {clar_exp}")
            print(f"  {Color.BOLD}Total: {total_score}/60{Color.END}")

        time.sleep(2)

        # Test Claude (if not skipped)
        if not self.skip_external and self.anthropic_client:
            print(f"\n{Color.BOLD}Testing Claude (Sonnet 3.5)...{Color.END}")
            claude_response = self.call_claude(question)

            if claude_response.get("error"):
                print(f"{Color.RED}❌ Error: {claude_response['error']}{Color.END}")
                results["systems"]["Claude"] = {"error": claude_response["error"]}
            else:
                answer = claude_response["answer"]

                # Evaluate
                fact_score, fact_exp = self.evaluate_factual_accuracy(answer, expected_facts)
                cons_score, cons_exp = self.evaluate_consistency(answer, avoid_phrases)
                rel_score, rel_exp = self.evaluate_relevance(question, answer)
                prof_score, prof_exp = self.evaluate_professionalism(answer)
                data_score, data_exp = self.evaluate_data_completeness(answer, question, False)
                clar_score, clar_exp = self.evaluate_clarity(answer)

                total_score = fact_score + cons_score + rel_score + prof_score + data_score + clar_score

                results["systems"]["Claude"] = {
                    "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                    "full_answer": answer,
                    "has_database_access": False,
                    "scores": {
                        "factual_accuracy": {"score": fact_score, "explanation": fact_exp},
                        "consistency": {"score": cons_score, "explanation": cons_exp},
                        "relevance": {"score": rel_score, "explanation": rel_exp},
                        "professionalism": {"score": prof_score, "explanation": prof_exp},
                        "data_completeness": {"score": data_score, "explanation": data_exp},
                        "clarity": {"score": clar_score, "explanation": clar_exp},
                        "total": total_score
                    }
                }

                print(f"  Factual Accuracy: {fact_score}/10")
                print(f"  Consistency: {cons_score}/10")
                print(f"  Relevance: {rel_score}/10")
                print(f"  Professionalism: {prof_score}/10")
                print(f"  Data Completeness: {data_score}/10")
                print(f"  Clarity: {clar_score}/10")
                print(f"  {Color.BOLD}Total: {total_score}/60{Color.END}")

            time.sleep(2)

        # Test ChatGPT (if not skipped)
        if not self.skip_external and self.openai_available:
            print(f"\n{Color.BOLD}Testing ChatGPT (GPT-4)...{Color.END}")
            chatgpt_response = self.call_chatgpt(question)

            if chatgpt_response.get("error"):
                print(f"{Color.RED}❌ Error: {chatgpt_response['error']}{Color.END}")
                results["systems"]["ChatGPT"] = {"error": chatgpt_response["error"]}
            else:
                answer = chatgpt_response["answer"]

                # Evaluate
                fact_score, fact_exp = self.evaluate_factual_accuracy(answer, expected_facts)
                cons_score, cons_exp = self.evaluate_consistency(answer, avoid_phrases)
                rel_score, rel_exp = self.evaluate_relevance(question, answer)
                prof_score, prof_exp = self.evaluate_professionalism(answer)
                data_score, data_exp = self.evaluate_data_completeness(answer, question, False)
                clar_score, clar_exp = self.evaluate_clarity(answer)

                total_score = fact_score + cons_score + rel_score + prof_score + data_score + clar_score

                results["systems"]["ChatGPT"] = {
                    "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                    "full_answer": answer,
                    "has_database_access": False,
                    "scores": {
                        "factual_accuracy": {"score": fact_score, "explanation": fact_exp},
                        "consistency": {"score": cons_score, "explanation": cons_exp},
                        "relevance": {"score": rel_score, "explanation": rel_exp},
                        "professionalism": {"score": prof_score, "explanation": prof_exp},
                        "data_completeness": {"score": data_score, "explanation": data_exp},
                        "clarity": {"score": clar_score, "explanation": clar_exp},
                        "total": total_score
                    }
                }

                print(f"  Factual Accuracy: {fact_score}/10")
                print(f"  Consistency: {cons_score}/10")
                print(f"  Relevance: {rel_score}/10")
                print(f"  Professionalism: {prof_score}/10")
                print(f"  Data Completeness: {data_score}/10")
                print(f"  Clarity: {clar_score}/10")
                print(f"  {Color.BOLD}Total: {total_score}/60{Color.END}")

        return results

    def run_all_scenarios(self):
        """Run all test scenarios"""
        self.print_header("BENCHMARK COMPARISON TEST SUITE")

        # Define test scenarios
        scenarios = [
            {
                "name": "Average Playtime Query",
                "question": "What's the average playtime for games priced at $20?",
                "expected_facts": ["hours", "20", "average"],
                "avoid_phrases": ["i think", "probably", "maybe"]
            },
            {
                "name": "Game Count Query",
                "question": "How many FPS games are on Steam?",
                "expected_facts": ["fps", "games"],
                "avoid_phrases": ["approximately", "around", "roughly"]
            },
            {
                "name": "Comparison Query",
                "question": "Should I price my game at $15 or $20?",
                "expected_facts": ["price", "playtime", "hours"],
                "avoid_phrases": ["it depends", "hard to say"]
            },
            {
                "name": "Consistency Test (Same Question Rephrased)",
                "question": "games that cost 20 dollars, what's their typical playtime?",
                "expected_facts": ["hours", "20"],
                "avoid_phrases": []
            },
            {
                "name": "Top Games Query",
                "question": "What are the top 3 most popular FPS games?",
                "expected_facts": ["fps", "game"],
                "avoid_phrases": []
            }
        ]

        for scenario in scenarios:
            results = self.run_scenario(scenario)
            self.results["test_scenarios"].append(results)

        self.calculate_overall_scores()
        self.print_summary()
        self.save_results()

    def calculate_overall_scores(self):
        """Calculate overall scores across all scenarios"""
        systems = ["PlayIntel"]

        if not self.skip_external:
            if self.anthropic_client:
                systems.append("Claude")
            if self.openai_available:
                systems.append("ChatGPT")

        overall_scores = {}

        for system in systems:
            total_score = 0
            scenario_count = 0

            for scenario in self.results["test_scenarios"]:
                if system in scenario["systems"] and "scores" in scenario["systems"][system]:
                    total_score += scenario["systems"][system]["scores"]["total"]
                    scenario_count += 1

            if scenario_count > 0:
                avg_score = total_score / scenario_count
                overall_scores[system] = {
                    "average_score": round(avg_score, 2),
                    "max_possible": 60,
                    "percentage": round((avg_score / 60) * 100, 1)
                }

        self.results["scoring"] = overall_scores

    def print_summary(self):
        """Print comparison summary"""
        self.print_header("BENCHMARK RESULTS SUMMARY")

        if not self.results["scoring"]:
            print(f"{Color.RED}No results to display{Color.END}")
            return

        print(f"{'System':<20} {'Avg Score':<15} {'Percentage':<15} {'Rating'}")
        print("-" * 70)

        # Sort by score
        sorted_systems = sorted(
            self.results["scoring"].items(),
            key=lambda x: x[1]["average_score"],
            reverse=True
        )

        for system, scores in sorted_systems:
            avg_score = scores["average_score"]
            percentage = scores["percentage"]

            # Determine rating
            if percentage >= 90:
                rating = f"{Color.GREEN}Excellent ⭐⭐⭐⭐⭐{Color.END}"
            elif percentage >= 80:
                rating = f"{Color.GREEN}Very Good ⭐⭐⭐⭐{Color.END}"
            elif percentage >= 70:
                rating = f"{Color.YELLOW}Good ⭐⭐⭐{Color.END}"
            elif percentage >= 60:
                rating = f"{Color.YELLOW}Fair ⭐⭐{Color.END}"
            else:
                rating = f"{Color.RED}Needs Work ⭐{Color.END}"

            print(f"{system:<20} {avg_score:.1f}/60{'':<8} {percentage}%{'':<9} {rating}")

        print()

        # Key findings
        if "PlayIntel" in self.results["scoring"]:
            playintel_score = self.results["scoring"]["PlayIntel"]["percentage"]

            print(f"{Color.BOLD}Key Findings:{Color.END}")
            print()

            if playintel_score >= 80:
                print(f"{Color.GREEN}✅ PlayIntel meets production quality standards{Color.END}")
            else:
                print(f"{Color.YELLOW}⚠️  PlayIntel needs improvements before production{Color.END}")

            # Compare to others if available
            if len(self.results["scoring"]) > 1:
                other_systems = [s for s in self.results["scoring"].keys() if s != "PlayIntel"]

                for other in other_systems:
                    other_score = self.results["scoring"][other]["percentage"]
                    diff = playintel_score - other_score

                    if diff > 10:
                        print(f"{Color.GREEN}✅ PlayIntel significantly outperforms {other} (+{diff:.1f}%){Color.END}")
                    elif diff > 0:
                        print(f"{Color.GREEN}✅ PlayIntel slightly better than {other} (+{diff:.1f}%){Color.END}")
                    elif diff > -10:
                        print(f"{Color.YELLOW}⚠️  PlayIntel comparable to {other} ({diff:+.1f}%){Color.END}")
                    else:
                        print(f"{Color.RED}❌ PlayIntel underperforms vs {other} ({diff:+.1f}%){Color.END}")

        print()

    def save_results(self):
        """Save results to JSON"""
        with open(RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"{Color.GREEN}✅ Results saved to: {RESULTS_FILE}{Color.END}")


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark PlayIntel vs Claude vs ChatGPT'
    )
    parser.add_argument(
        '--playintel-only',
        action='store_true',
        help='Test only PlayIntel (skip Claude and ChatGPT)'
    )

    args = parser.parse_args()

    print(f"\n{Color.BLUE}{Color.BOLD}🏆 Starting Benchmark Comparison Tests{Color.END}\n")

    if args.playintel_only:
        print(f"{Color.YELLOW}Running PlayIntel only (skipping external APIs){Color.END}\n")
    else:
        print("Comparing PlayIntel vs Claude vs ChatGPT\n")
        if not ANTHROPIC_API_KEY:
            print(f"{Color.YELLOW}⚠️  ANTHROPIC_API_KEY not set - will skip Claude{Color.END}")
        if not OPENAI_API_KEY:
            print(f"{Color.YELLOW}⚠️  OPENAI_API_KEY not set - will skip ChatGPT{Color.END}")
        print()

    test = BenchmarkTest(skip_external=args.playintel_only)
    test.run_all_scenarios()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}⚠️  Tests interrupted{Color.END}")
    except Exception as e:
        print(f"\n{Color.RED}❌ Fatal error: {e}{Color.END}")
        import traceback
        traceback.print_exc()
