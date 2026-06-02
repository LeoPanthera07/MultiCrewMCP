"""Main entry point for running the Operations Assistant CrewAI CLI."""

import sys
from crew.crew import build_and_run

if __name__ == "__main__":
    # If a question is provided in CLI arguments, join them. Otherwise, prompt the user.
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Question: ")
    
    # Run the crew orchestration
    result = build_and_run(question)
    
    print("\n=== FINAL ANSWER ===")
    print(result)
