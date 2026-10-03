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

# 4. Function: Run pytest and capture results using subprocess
def runTests(testFilePath: str) -> Tuple[bool, str]:
    """
    Executes pytest programmatically and returns:
    - bool: True if tests passed (returncode 0), False otherwise.
    - str: The captured test output (traceback and assertion details).
    """
    print(f"🧪 Running tests via: pytest {testFilePath}...")
    
    executionResult = subprocess.run(
        ["pytest", testFilePath],
        capture_output=True,
        text=True
    )
    
    testsPassed = (executionResult.returncode == 0)
    # If failed, capture stdout (pytest prints assertion failures to stdout)
    testOutput = executionResult.stdout if not testsPassed else "All tests passed successfully."
    return testsPassed, testOutput

# 5. Function: Consult Gemini for a surgical fix
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

# 6. Main Orchestrator: The Closed-Loop Self-Healing Agent
def healSourceFile(sourceFilePath: str, testFilePath: str, maxAttempts: int = 3) -> bool:
    """
    Orchestrates the ReAct self-healing loop:
    Test -> Diagnose -> Patch -> Re-test.
    """
    print("\n" + "="*50)
    print(f"🩺 GitHealer initiated for: {sourceFilePath}")
    print(f"🎯 Target test suite:      {testFilePath}")
    print("="*50 + "\n")
    
    attemptCount = 1
    
    while attemptCount <= maxAttempts:
        print(f"\n--- [Iteration {attemptCount} of {maxAttempts}] ---")
        
        # Step A: Observe (Run tests)
        testsPassed, testOutput = runTests(testFilePath)
        
        if testsPassed:
            print("✅ All tests PASSED! The code is healthy.")
            return True
        
        print("❌ Tests FAILED. Extracting failure trace...")
        
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
        
    # If the loop finishes without passing:
    print(f"\n⚠️ GitHealer reached max attempts ({maxAttempts}) without passing all tests.")
    return False

# 7. Entry point
if __name__ == "__main__":
    targetSourceFile = "discountCalculator.py"
    targetTestFile = "testDiscountCalculator.py"
    
    success = healSourceFile(targetSourceFile, targetTestFile, maxAttempts=3)
    
    if success:
        print("\n🎉 SUCCESS: GitHealer successfully cured the code!")
    else:
        print("\n❌ FAILED: Could not resolve all test failures automatically.")