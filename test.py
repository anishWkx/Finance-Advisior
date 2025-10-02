import argparse
from query_data import query_rag
from langchain_ollama import OllamaLLM as Ollama

EVAL_PROMPT = """
Expected Response: {expected_response}
Actual Response: {actual_response}
---
(Answer with 'true' or 'false') Does the actual response match the expected response? 
"""

# Global flag for pinecone usage
USE_PINECONE = False

def test_emergency_fund():
    assert query_and_validate(
        question="How many months of expenses should you have in an emergency fund?",
        expected_response="3-6 months of expenses",
    )


def test_rule_of_72():
    assert query_and_validate(
        question="What is the Rule of 72 and how do you use it?",
        expected_response="The Rule of 72 estimates how long it takes to double your money. Divide 72 by your annual interest rate.",
    )


def test_compound_interest():
    assert query_and_validate(
        question="What is compound interest?",
        expected_response="Interest earned on both the original principal and previously earned interest.",
    )


def test_pe_ratio():
    assert query_and_validate(
        question="What does P/E ratio stand for and how is it calculated?",
        expected_response="Price-to-Earnings ratio. It's calculated by dividing stock price by earnings per share.",
    )


def test_diversification():
    assert query_and_validate(
        question="What is diversification in investing?",
        expected_response="Spreading investments across different asset classes, sectors, or securities to reduce risk.",
    )


# Inverted questions (should fail)
def test_rule_of_72_wrong():
    assert not query_and_validate(
        question="What is the Rule of 72 and how do you use it?",
        expected_response="The Rule of 72 is used to calculate tax deductions.",  # Completely wrong
    )


def test_compound_interest_wrong():
    assert not query_and_validate(
        question="What is compound interest?",
        expected_response="A type of bank account that requires a minimum balance.",  # Wrong definition
    )


def query_and_validate(question: str, expected_response: str):
    print("\n" + "="*80)
    print(f"Question: {question}")
    print("="*80)
    
    response_text = query_rag(question, use_pinecone=USE_PINECONE)
    prompt = EVAL_PROMPT.format(
        expected_response=expected_response, actual_response=response_text
    )

    model = Ollama(model="llama2")
    evaluation_results_str = model.invoke(prompt)
    evaluation_results_str_cleaned = evaluation_results_str.strip().lower()

    print(prompt)
    print("-" * 40)

    if "true" in evaluation_results_str_cleaned:
        # Print response in Green if it is correct.
        print("\033[92m" + f"✅ PASS: {evaluation_results_str_cleaned}" + "\033[0m")
        return True
    elif "false" in evaluation_results_str_cleaned:
        # Print response in Red if it is incorrect.
        print("\033[91m" + f"❌ FAIL: {evaluation_results_str_cleaned}" + "\033[0m")
        return False
    else:
        raise ValueError(
            f"Invalid evaluation result. Cannot determine if 'true' or 'false'."
        )


def main():
    global USE_PINECONE
    
    parser = argparse.ArgumentParser(description="Run RAG tests")
    parser.add_argument("--pinecone", action="store_true", help="Use Pinecone instead of Chroma")
    args = parser.parse_args()
    
    USE_PINECONE = args.pinecone
    
    print(f"🔍 Using {'Pinecone' if USE_PINECONE else 'Chroma'} for tests...")
    
    # List of all tests
    tests = [
        ("test_emergency_fund", test_emergency_fund),
        ("test_rule_of_72", test_rule_of_72),
        ("test_compound_interest", test_compound_interest),
        ("test_pe_ratio", test_pe_ratio),
        ("test_diversification", test_diversification),
        ("test_rule_of_72_wrong", test_rule_of_72_wrong),
        ("test_compound_interest_wrong", test_compound_interest_wrong),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name}...")
            test_func()
            print(f"✅ {test_name} PASSED")
            passed += 1
        except AssertionError:
            print(f"❌ {test_name} FAILED")
            failed += 1
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    print("🎉 All tests completed!")


if __name__ == "__main__":
    main()