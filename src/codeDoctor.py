import os
from typing import Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Load environment variables
load_dotenv()

# 2. Define the Pydantic schema for the diagnostic report
class DiagnosticReport(BaseModel):
    rootCause: str = Field(
        description="Detailed technical explanation of what caused the bug or test failure"
    )
    failingLineNumber: int = Field(
        description="The line number in the source code where the error originates"
    )
    severityLevel: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        description="Severity level of the detected issue"
    )
    suggestedFixStrategy: str = Field(
        description="Step-by-step strategy to resolve the issue without breaking other features"
    )
    proposedCode: str = Field(
        description="The complete corrected replacement code for the broken function or block"
    )

# 3. Initialize Gemini client
geminiClient = genai.Client()

# 4. A simulated broken function to test our doctor
brokenCodeSnippet = """
def divideNumbers(dividend: float, divisor: float) -> float:
    # BUG: No validation for division by zero
    result = dividend / divisor
    return result
"""

failingErrorMessage = "ZeroDivisionError: float division by zero at line 4 in divideNumbers"

print("GitHealer CodeDoctor is diagnosing the bug...\n")

# 5. Prompt instructing the model to act as a diagnostic engine
diagnosticPrompt = f"""
You are GitHealer's surgical code doctor.
Analyze the following broken code snippet and the associated error trace:

--- BROKEN CODE ---
{brokenCodeSnippet}

--- ERROR TRACE ---
{failingErrorMessage}

Provide a precise, structured diagnostic report and the repaired code.
"""

# 6. Request to Gemini enforcing the Pydantic schema
modelResponse = geminiClient.models.generate_content(
    model="gemini-3.8-flash",
    contents=diagnosticPrompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=DiagnosticReport,
        temperature=0.1,  # Low temperature = high determinism and precision
    ),
)

# 7. Accessing the structured response directly as a Python object!
# The SDK automatically parses the JSON into our Pydantic model:
diagnosticData: DiagnosticReport = modelResponse.parsed

# 8. Display the structured results
print(f"Severity:      {diagnosticData.severityLevel}")
print(f"Failing Line:  {diagnosticData.failingLineNumber}")
print(f"Root Cause:    {diagnosticData.rootCause}")
print(f"Strategy:      {diagnosticData.suggestedFixStrategy}")
print("\n Proposed Fixed Code:")
print(diagnosticData.proposedCode)