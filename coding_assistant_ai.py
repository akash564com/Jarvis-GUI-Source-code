#!/usr/bin/env python3
"""
Coding Assistant AI 🤖
A personal Python coding assistant built with open-source models.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MEMORY_FILE = Path("coding_assistant_memory.json")
OUTPUT_FILE = Path("generated_solution.py")
TEST_FILE = Path("test_generated_solution.py")


@dataclass
class AssistantReply:
    code: str
    explanation: str


class MemoryStore:
    def __init__(self, path: Path = MEMORY_FILE) -> None:
        self.path = path
        self.path.touch(exist_ok=True)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.read_text(encoding="utf-8").strip():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, history: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    def add(self, query: str, reply: AssistantReply) -> None:
        history = self.load()
        history.append(
            {
                "query": query,
                "explanation": reply.explanation,
                "code": reply.code,
            }
        )
        self.save(history)


class CodingAssistant:
    def __init__(self) -> None:
        self.memory = MemoryStore()

    def _mentor_tone(self, query: str) -> str:
        return (
            "Great question! Let's solve this step by step like a coding mentor. "
            f"You asked: '{query}'. I will keep the code clean and beginner-friendly."
        )

    def generate(self, query: str) -> AssistantReply:
        # Plug in any open-source model (e.g. CodeLlama/DeepSeek-Coder via transformers or Ollama).
        # This baseline keeps the project runnable out-of-the-box without heavy model dependencies.
        if "fibonacci" in query.lower():
            code = textwrap.dedent(
                """
                def fibonacci(n: int) -> int:
                    if n < 0:
                        raise ValueError("n must be non-negative")
                    if n in (0, 1):
                        return n
                    a, b = 0, 1
                    for _ in range(2, n + 1):
                        a, b = b, a + b
                    return b
                """
            ).strip()
        else:
            code = textwrap.dedent(
                """
                def solve() -> str:
                    return "Hello from Coding Assistant AI!"
                """
            ).strip()

        explanation = self._mentor_tone(query)
        return AssistantReply(code=code, explanation=explanation)

    def save_code(self, code: str, output: Path = OUTPUT_FILE) -> None:
        output.write_text(code + "\n", encoding="utf-8")

    def create_smoke_test(self, output: Path = OUTPUT_FILE, test_output: Path = TEST_FILE) -> None:
        test_code = textwrap.dedent(
            f"""
            import importlib.util


            def _load_module():
                spec = importlib.util.spec_from_file_location("generated_solution", "{output}")
                module = importlib.util.module_from_spec(spec)
                assert spec and spec.loader
                spec.loader.exec_module(module)
                return module


            def test_generated_symbol_exists():
                mod = _load_module()
                assert hasattr(mod, "solve") or hasattr(mod, "fibonacci")
            """
        ).strip()
        test_output.write_text(test_code + "\n", encoding="utf-8")

    def run_tests(self, test_file: Path = TEST_FILE) -> tuple[int, str]:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file)],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode, result.stdout + "\n" + result.stderr
        except FileNotFoundError:
            return 127, "pytest not installed. Install with: pip install pytest"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coding Assistant AI")
    parser.add_argument("query", help="What Python code do you want to generate?")
    parser.add_argument("--skip-tests", action="store_true", help="Do not auto-run tests")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assistant = CodingAssistant()

    reply = assistant.generate(args.query)
    assistant.save_code(reply.code)
    assistant.create_smoke_test()
    assistant.memory.add(args.query, reply)

    print("\n🧠 Mentor Explanation")
    print(reply.explanation)
    print("\n🐍 Generated Python Code")
    print(reply.code)
    print(f"\nSaved to: {OUTPUT_FILE}")

    if not args.skip_tests:
        rc, output = assistant.run_tests()
        print("\n🧪 Test Output")
        print(output)
        return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
