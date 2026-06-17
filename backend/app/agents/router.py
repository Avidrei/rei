import json
from google import genai
from google.genai import types
from app.config import settings
from app.services.tool_service import tool_service

class REIAgentRouter:
    def __init__(self):
        # Initializing the modern Google GenAI Client (100% free-tier compliant)
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # Using Gemini 2.5 Flash - optimized for extremely fast structured json generation
        self.model_name = "gemini-2.5-flash"

    def determine_routing_plan(self, user_query: str) -> dict:
        """
        Inspects the active database schema dynamically, passes state to Gemini, 
        and extracts a highly accurate structural JSON orchestration map.
        """
        # Fetch current column data layouts dynamically so Gemini knows what keys are real
        dataset_profile = tool_service.profile_dataset()
        
        system_instruction = f"""
        You are the primary cognitive routing engine of REI, which stands explicitly for Retrieval & Execution Interface.
        Your job is to analyze the user's natural language query relative to the currently active dataset profile, and choose the optimal tool execution track.

        IDENTITY & MISSION:
        - You are the vanguard of the Retrieval & Execution Interface. Your thought traces should reflect absolute technical precision.
        - You balance semantic memory recall (Retrieval) and mathematical data manipulation (Execution).

        ACTIVE DATASET PROFILE MATRIX:
        {json.dumps(dataset_profile, indent=2)}

        ROUTING TRACK INSTRUCTIONS (Choose exactly ONE):
        1. "DIRECT": The query is conversational, a greeting, system diagnostics check, small talk, or generalized knowledge completely independent of the dataset.
        2. "RAG": The user is asking about semantic notes, textual entries, qualitative values, descriptions, or concepts embedded inside text records.
        3. "TOOL": The user wants quantitative math calculations (averages, maximums, minimums, standard deviation), item distributions, value correlations, row counts, or strict logical column filtering.
        4. "HYBRID": The query requires a combination of semantic matching followed by numerical calculation or structured formatting.

        CRITICAL SCHEMA MATCHING & OPERATOR INSTRUCTIONS:
        - Schema Alignment: Look at the column names available in the ACTIVE DATASET PROFILE. If a user asks for a feature using shorthand or variation (e.g., "grades", "price", "gpa"), normalize it to the exact case-sensitive column string matching the profile metadata.
        - Operator Suite: If track is "TOOL", select the most fitting operator option from this strict pool: ["==", "!=", ">", "<", ">=", "<=", "contains"].
        - Guardrail Rule: If a user attempts a quantitative analysis against a column that does NOT exist in the provided profile matrix, route the request to "DIRECT" and explicitly state the schema limitation in your `reasoning_trace`.

        You must return a raw JSON object matching this structure exactly:
        {{
            "reasoning_trace": "[REI_ROUTER_INFERENCE]: Explicit statement explaining the track selection, schema validation checks, and operational choices.",
            "track": "DIRECT" | "RAG" | "TOOL" | "HYBRID",
            "suggested_top_k": 3,
            "filter_column": "exact_case_sensitive_column_name_or_null",
            "filter_operator": "== | != | > | < | >= | <= | contains | null",
            "filter_value": "extracted_value_or_null"
        }}
        """

        try:
            # Call Gemini enforcing JSON structured outputs matching a response schema rule
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1 # Ultra-low temperature ensures highly predictable, deterministic routing execution
                )
            )
            
            # Safely transform response string directly into an operational dictionary
            routing_decision = json.loads(response.text)
            return routing_decision
            
        except Exception as e:
            # Fallback gracefully to standard DIRECT messaging trace if parsing failures occur
            return {
                "reasoning_trace": f"[REI_FAULT_PROTECTION]: Routing engine hit an execution boundary exception: {str(e)}. Falling back to direct conversational mode.",
                "track": "DIRECT",
                "suggested_top_k": 3,
                "filter_column": None,
                "filter_operator": None,
                "filter_value": None
            }

# Register singleton instance
agent_router = REIAgentRouter()