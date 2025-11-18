#!/usr/bin/env python
"""Test Azure OpenAI GPT-4.1 fallback"""
import sys

from corrector.model import AzureOpenAICorrector
from corrector.prompt import load_base_prompt
from corrector.text_utils import Token

# Simple test tokens (id, text, start, end, kind, line)
tokens = [
    Token(0, "El", 0, 2, "word", 1),
    Token(1, " ", 2, 3, "space", 1),
    Token(2, "niño", 3, 7, "word", 1),
    Token(3, " ", 7, 8, "space", 1),
    Token(4, "rio", 8, 11, "word", 1),  # Missing tilde
    Token(5, " ", 11, 12, "space", 1),
    Token(6, "con", 12, 15, "word", 1),
    Token(7, " ", 15, 16, "space", 1),
    Token(8, "ganas", 16, 21, "word", 1),
    Token(9, ".", 21, 22, "punct", 1),
]

print("Testing Azure OpenAI GPT-5 -> GPT-4.1 fallback...")
print("=" * 60)

try:
    base_prompt = load_base_prompt()
    corrector = AzureOpenAICorrector(base_prompt_text=base_prompt)

    print(f"Input text: {' '.join(t.text for t in tokens)}")
    print("\nCalling Azure OpenAI...")
    print("(If GPT-5 hits content filter, will automatically try GPT-4.1)\n")

    corrections = corrector.correct_tokens(tokens)

    print(f"✅ Success! Found {len(corrections)} corrections:")
    for c in corrections:
        print(f"  • Token {c.token_id}: '{c.original}' → '{c.replacement}'")
        print(f"    Reason: {c.reason}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Azure fallback test passed!")
