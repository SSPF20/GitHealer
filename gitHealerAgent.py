import os
import subprocess
from typing import Literal, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Load environment variables
load_dotenv()

# 2. Pydantic schema for the structured patch response
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

# 7. Main Orchestrator: The Closed-Loop Self-Healing Agent
def healSourceFile(sourceFilePath: str, testFilePath: str, maxAttempts: int = 3) -> bool:
    """
    Orchestrates the ReAct self-healing loop inside the Sandbox:
    Sandboxed Test -> Diagnose -> Patch -> Re-test.
    """
    print("\n" + "="*55)
    print(f"🩺 GitHealer Sandbox Agent initiated for: {sourceFilePath}")
    print(f"🎯 Target test suite:                    {testFilePath}")
    print("="*55 + "\n")
    
    attemptCount = 1
    
    while attemptCount <= maxAttempts:
        print(f"\n--- [Iteration {attemptCount} of {maxAttempts}] ---")
        
        # Step A: Observe inside Docker Sandbox
        testsPassed, testOutput = runTests(testFilePath, useSandbox=True)
        
        if testsPassed:
            print("✅ All tests PASSED inside the Sandbox! Code is healthy.")
            return True
        
        print("❌ Tests FAILED inside the Sandbox. Extracting failure trace...")
        
        # Step B: Read current broken file from disk
        with open(sourceFilePath, "r") as file:
            currentCode = file.read()
            
        # Step C: Reason (Gemini diagnosis and patch generation)
        healData: HealReport = requestHealPatch(currentCode, testOutput, attemptCount)
        
        print(f"\n🔍 Diagnosis: {healData.rootCause}")
        print(f"💡 Strategy:  {healData.suggestedFixStrategy}")
        print(f"⚡ Severity:  {healData.severityLevel}")
        
        # Step D: Act (Apply the patch directly to the file)
        print(f"🩹 Applying surgical patch to {sourceFilePath}...")
        with open(sourceFilePath, "w") as file:
            file.write(healData.fixedSourceCode)
            
        attemptCount += 1
        
    print(f"\n⚠️ GitHealer reached max attempts ({maxAttempts}) without passing all tests.")
    return False

# 8. Entry point
if __name__ == "__main__":
    targetSourceFile = "discountCalculator.py"
    targetTestFile = "testDiscountCalculator.py"
    
    success = healSourceFile(targetSourceFile, targetTestFile, maxAttempts=3)
    
    if success:
        print("\n🎉 SUCCESS: GitHealer successfully cured the code inside the Sandbox!")
    else:
        print("\n❌ FAILED: Could not resolve all test failures automatically.")