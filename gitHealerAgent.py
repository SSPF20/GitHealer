import os
import sys
import argparse
import subprocess
from typing import Literal, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Load environment variables
load_dotenv()

# 2. Pydantic schema for structured patch response
class HealReport(BaseModel):
    rootCause: str = Field(
        description="Explanation of why the test failed"
    )
    severityLevel: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        description="Severity assessment of the bug"
    )
    suggestedFixStrategy: str = Field(
        description="Technical strategy applied to heal the bug"
    )
    fixedSourceCode: str = Field(
        description="The complete, working source code of the entire file with the bug fixed"
    )

# 3. Initialize Gemini client
geminiClient = genai.Client()

# 4. Helper: Check if Docker daemon is available
def isDockerAvailable() -> bool:
    """Checks whether Docker daemon is active and accessible."""
    try:
        checkResult = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )
        return checkResult.returncode == 0
    except FileNotFoundError:
        return False

# 5. Function: Run tests with Docker Sandbox or local fallback
def runTests(testFilePath: str, useSandbox: bool = True) -> Tuple[bool, str]:
    """
    Executes pytest either inside an isolated Docker sandbox or locally as fallback.
    Returns:
    - bool: True if tests passed, False otherwise.
    - str: Captured failure output (traceback).
    """
    currentDirectory = os.getcwd()
    dockerReady = isDockerAvailable()

    if useSandbox and dockerReady:
        print(f"🛡️  Running tests inside isolated Docker Sandbox (--network none)...")
        commandToExecute = [
            "docker", "run", "--rm",
            "-v", f"{currentDirectory}:/app",
            "-w", "/app",
            "--network", "none",
            "--memory", "512m",
            "git-healer-sandbox",
            "pytest", testFilePath
        ]
    else:
        if useSandbox and not dockerReady:
            print("⚠️  Docker unavailable. Falling back to local subprocess...")
        else:
            print(f"🧪 Running tests locally via subprocess: {testFilePath}...")
        commandToExecute = ["pytest", testFilePath]
    
    executionResult = subprocess.run(
        commandToExecute,
        capture_output=True,
        text=True
    )
    
    testsPassed = (executionResult.returncode == 0)
    testOutput = executionResult.stdout if not testsPassed else "All tests passed successfully."
    return testsPassed, testOutput

# 6. Function: Consult Gemini for a surgical fix
def requestHealPatch(sourceCode: str, testFailureTrace: str, attemptNumber: int) -> HealReport:
    """
    Sends the broken code and test failure trace to Gemini using structured output.
    """
    print(f"🤖 Consulting Gemini 3.8 Flash (Attempt #{attemptNumber})...")
    
    healingPrompt = f"""
    You are GitHealer, an autonomous surgical code repair agent.
    A unit test has failed. Your task is to repair the source code so that all tests pass.

    --- CURRENT SOURCE CODE ---
    {sourceCode}

    --- TEST FAILURE TRACE ---
    {testFailureTrace}

    Instructions:
    1. Analyze the exact assertion failure and root cause.
    2. Provide the ENTIRE repaired source code in the `fixedSourceCode` field.
    3. Ensure you do NOT break existing valid functionality.
    """
    
    modelResponse = geminiClient.models.generate_content(
        model="gemini-3.8-flash",
        contents=healingPrompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=HealReport,
            temperature=0.1,
        ),
    )
    
    return modelResponse.parsed

# 7. Command: Scan (Dry-Run Diagnostic only)
def scanSourceFile(sourceFilePath: str, testFilePath: str, useSandbox: bool = True) -> bool:
    """
    Runs a non-destructive diagnostic scan. Reports findings without modifying files.
    """
    print("\n" + "="*55)
    print(f"🩺 GitHealer Diagnostic Scan (Dry-Run): {sourceFilePath}")
    print(f"🎯 Target test suite:                   {testFilePath}")
    print("="*55 + "\n")

    testsPassed, testOutput = runTests(testFilePath, useSandbox=useSandbox)
    
    if testsPassed:
        print("✅ Code is healthy! All tests passed without issues.")
        return True

    print("❌ Test failure detected. Generating diagnosis...\n")
    
    with open(sourceFilePath, "r") as file:
        currentCode = file.read()
        
    diagnosticData: HealReport = requestHealPatch(currentCode, testOutput, attemptNumber=1)
    
    print("\n--- Diagnostic Findings ---")
    print(f"📌 Severity: {diagnosticData.severityLevel}")
    print(f"🔍 Root Cause:\n{diagnosticData.rootCause}\n")
    print(f"💡 Recommended Strategy:\n{diagnosticData.suggestedFixStrategy}\n")
    print("📋 Proposed Code (Dry-Run, not applied to disk):")
    print("-" * 40)
    print(diagnosticData.fixedSourceCode)
    print("-" * 40)
    return False

# 8. Command: Heal (Closed-Loop Autonomous Repair)
def healSourceFile(sourceFilePath: str, testFilePath: str, maxAttempts: int = 3, useSandbox: bool = True) -> bool:
    """
    Orchestrates the ReAct self-healing loop:
    Test -> Diagnose -> Patch -> Re-test.
    """
    print("\n" + "="*55)
    print(f"🩺 GitHealer Autonomous Repair initiated for: {sourceFilePath}")
    print(f"🎯 Target test suite:                         {testFilePath}")
    print("="*55 + "\n")
    
    attemptCount = 1
    
    while attemptCount <= maxAttempts:
        print(f"\n--- [Iteration {attemptCount} of {maxAttempts}] ---")
        
        testsPassed, testOutput = runTests(testFilePath, useSandbox=useSandbox)
        
        if testsPassed:
            print("✅ All tests PASSED! The codebase is healthy.")
            return True
        
        print("❌ Tests FAILED. Extracting failure trace...")
        
        with open(sourceFilePath, "r") as file:
            currentCode = file.read()
            
        healData: HealReport = requestHealPatch(currentCode, testOutput, attemptCount)
        
        print(f"\n🔍 Diagnosis: {healData.rootCause}")
        print(f"💡 Strategy:  {healData.suggestedFixStrategy}")
        print(f"⚡ Severity:  {healData.severityLevel}")
        
        print(f"🩹 Applying surgical patch to {sourceFilePath}...")
        with open(sourceFilePath, "w") as file:
            file.write(healData.fixedSourceCode)
            
        attemptCount += 1
        
    print(f"\n⚠️ GitHealer reached max attempts ({maxAttempts}) without passing all tests.")
    return False

# 9. CLI Entry Point with argparse
def main():
    cliParser = argparse.ArgumentParser(
        prog="git-healer",
        description="🩺 GitHealer: Autonomous Code Review & Self-Healing Agent powered by Google Gemini",
        epilog="Example: python gitHealerAgent.py heal discountCalculator.py testDiscountCalculator.py"
    )
    
    subParsers = cliParser.add_subparsers(dest="command", required=True, help="Sub-command to execute")
    
    # --- SUBCOMMAND: heal ---
    healParser = subParsers.add_parser("heal", help="Autonomously diagnose, patch, and verify code until tests pass")
    healParser.add_argument("source_file", help="Path to the source code file to repair")
    healParser.add_argument("test_file", help="Path to the test file to verify against")
    healParser.add_argument("--max-attempts", type=int, default=3, help="Maximum self-healing attempts (default: 3)")
    healParser.add_argument("--no-sandbox", action="store_true", help="Bypass Docker and run tests directly on local host")
    
    # --- SUBCOMMAND: scan ---
    scanParser = subParsers.add_parser("scan", help="Run a dry-run diagnostic scan without modifying files on disk")
    scanParser.add_argument("source_file", help="Path to the source code file to diagnose")
    scanParser.add_argument("test_file", help="Path to the test file to verify against")
    scanParser.add_argument("--no-sandbox", action="store_true", help="Bypass Docker and run tests directly on local host")
    
    args = cliParser.parse_args()
    
    useSandboxMode = not args.no_sandbox
    
    if args.command == "heal":
        success = healSourceFile(
            sourceFilePath=args.source_file,
            testFilePath=args.test_file,
            maxAttempts=args.max_attempts,
            useSandbox=useSandboxMode
        )
        sys.exit(0 if success else 1)
        
    elif args.command == "scan":
        healthy = scanSourceFile(
            sourceFilePath=args.source_file,
            testFilePath=args.test_file,
            useSandbox=useSandboxMode
        )
        sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    main()