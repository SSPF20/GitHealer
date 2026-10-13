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

# 2. Pydantic schema for targeted patch response
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

# 3. Pydantic schema for autonomous repository-wide discovery and healing
class AutoDiscoveryReport(BaseModel):
    brokenSourceFilePath: str = Field(
        description="The relative path to the broken source file that caused the failure (e.g. 'discountCalculator.py')"
    )
    failingTestFilePath: str = Field(
        description="The relative path to the test file that failed (e.g. 'tests/testDiscountCalculator.py')"
    )
    rootCause: str = Field(
        description="Detailed technical explanation of what caused the test failure"
    )
    severityLevel: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        description="Severity assessment of the detected issue"
    )
    suggestedFixStrategy: str = Field(
        description="Strategy to heal the issue without causing regressions"
    )
    fixedSourceCode: str = Field(
        description="The complete, working source code of the entire broken file with the bug fixed"
    )

# 4. Initialize Gemini client
geminiClient = genai.Client()

# 5. Helper: Check if Docker daemon is available
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

# 6. Function: Run specific tests with Docker Sandbox or local fallback
def runTests(testFilePath: str, useSandbox: bool = True) -> Tuple[bool, str]:
    """
    Executes a specific test file either inside an isolated Docker sandbox or locally.
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

# 7. Function: Run global test suite across the entire repository
def runGlobalTests(useSandbox: bool = True) -> Tuple[bool, str]:
    """
    Executes pytest across the entire repository.
    """
    currentDirectory = os.getcwd()
    dockerReady = isDockerAvailable()

    if useSandbox and dockerReady:
        print("🛡️  Running global test suite inside Docker Sandbox (--network none)...")
        commandToExecute = [
            "docker", "run", "--rm",
            "-v", f"{currentDirectory}:/app",
            "-w", "/app",
            "--network", "none",
            "--memory", "512m",
            "git-healer-sandbox",
            "pytest"
        ]
    else:
        if useSandbox and not dockerReady:
            print("⚠️  Docker unavailable. Falling back to local subprocess...")
        else:
            print("🧪 Running global test suite locally via subprocess...")
        commandToExecute = ["pytest"]

    executionResult = subprocess.run(
        commandToExecute,
        capture_output=True,
        text=True
    )

    testsPassed = (executionResult.returncode == 0)
    testOutput = executionResult.stdout if not testsPassed else "All tests passed successfully."
    return testsPassed, testOutput

# 8. Function: Consult Gemini for a surgical fix on a known file
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

# 9. Command: Scan (Dry-Run Diagnostic only)
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

# 10. Command: Heal (Closed-Loop Targeted Repair)
def healSourceFile(sourceFilePath: str, testFilePath: str, maxAttempts: int = 3, useSandbox: bool = True) -> bool:
    """
    Orchestrates targeted self-healing loop:
    Test -> Diagnose -> Patch -> Re-test.
    """
    print("\n" + "="*55)
    print(f"🩺 GitHealer Targeted Repair initiated for: {sourceFilePath}")
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

# 11. Command: Auto (Autonomous Repository-Wide Auto-Healing)
def autoHealRepository(maxAttempts: int = 3, useSandbox: bool = True) -> bool:
    """
    Fully autonomous repository-wide healing:
    1. Runs the entire global test suite.
    2. If all tests pass, exits immediately.
    3. If any test fails, Gemini auto-discovers which source file is broken and generates a patch.
    4. Applies the patch and re-tests until all repository tests pass.
    """
    print("\n" + "="*60)
    print("🩺 GitHealer Autonomous Repository Auto-Healing Mode")
    print("="*60 + "\n")

    attemptCount = 1

    while attemptCount <= maxAttempts:
        print(f"\n--- [Auto-Healing Cycle {attemptCount} of {maxAttempts}] ---")
        testsPassed, testOutput = runGlobalTests(useSandbox=useSandbox)

        if testsPassed:
            print("\n✅ SUCCESS: All tests in the repository PASSED! Codebase is healthy.")
            return True

        print("❌ Failures detected in test suite. Consulting Gemini for auto-discovery...")

        autoPrompt = f"""
        You are GitHealer, an autonomous repository repair agent.
        The global test suite in this repository has failed.

        --- GLOBAL TEST SUITE FAILURE TRACE ---
        {testOutput}

        Instructions:
        1. Analyze the traceback to identify the exact relative broken source file path (e.g. 'discountCalculator.py').
        2. Identify the failing test file path (e.g. 'tests/testDiscountCalculator.py').
        3. Explain the root cause and severity.
        4. Provide the ENTIRE repaired source code for the broken file in `fixedSourceCode`.
        """

        modelResponse = geminiClient.models.generate_content(
            model="gemini-3.8-flash",
            contents=autoPrompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AutoDiscoveryReport,
                temperature=0.1,
            ),
        )

        autoData: AutoDiscoveryReport = modelResponse.parsed

        print(f"\n🎯 Auto-Discovered Broken File: {autoData.brokenSourceFilePath}")
        print(f"🧪 Associated Failing Test:    {autoData.failingTestFilePath}")
        print(f"🔍 Root Cause:                  {autoData.rootCause}")
        print(f"💡 Strategy:                    {autoData.suggestedFixStrategy}")
        print(f"⚡ Severity:                    {autoData.severityLevel}")

        targetPath = autoData.brokenSourceFilePath.strip().lstrip("/")
        if not os.path.exists(targetPath):
            altPath = os.path.basename(targetPath)
            if os.path.exists(altPath):
                targetPath = altPath

        print(f"🩹 Applying surgical patch to: {targetPath}...")
        with open(targetPath, "w") as file:
            file.write(autoData.fixedSourceCode)

        attemptCount += 1

    print(f"\n⚠️ GitHealer reached max attempts ({maxAttempts}) without achieving full repository health.")
    return False

# 12. CLI Entry Point with argparse
def main():
    cliParser = argparse.ArgumentParser(
        prog="git-healer",
        description="🩺 GitHealer: Autonomous Code Review & Self-Healing Agent powered by Google Gemini",
        epilog="Examples:\n  python src/gitHealerAgent.py auto\n  python src/gitHealerAgent.py heal discountCalculator.py tests/testDiscountCalculator.py"
    )
    
    subParsers = cliParser.add_subparsers(dest="command", required=True, help="Sub-command to execute")
    
    # --- SUBCOMMAND: auto ---
    autoParser = subParsers.add_parser(
        "auto",
        help="Autonomously detect any failing tests in the repository and heal the broken files"
    )
    autoParser.add_argument("--max-attempts", type=int, default=3, help="Maximum healing iterations (default: 3)")
    autoParser.add_argument("--no-sandbox", action="store_true", help="Bypass Docker and run tests directly on local host")

    # --- SUBCOMMAND: heal ---
    healParser = subParsers.add_parser("heal", help="Autonomously diagnose, patch, and verify a specific target file")
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
    
    if args.command == "auto":
        success = autoHealRepository(
            maxAttempts=args.max_attempts,
            useSandbox=useSandboxMode
        )
        sys.exit(0 if success else 1)

    elif args.command == "heal":
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