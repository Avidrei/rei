from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import shutil
import json
from google import genai
from google.genai import types

from app.config import settings
from app.services.rag_service import rag_service
from app.services.tool_service import tool_service
from app.agents.router import agent_router
from app.services.memory_service import memory_service

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AssistantConfig(BaseModel):
    personality: str = Field(default="technical", description="Options: 'technical', 'casual', 'friendly', 'minimalist'")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="Controls LLM response creativity")

# Formal input validation schema for runtime execution
class ChatRequest(BaseModel):
    message: str
    config: AssistantConfig = AssistantConfig()

@app.post("/api/chat")
async def centralized_agentic_chat(payload: ChatRequest):
    user_message = payload.message
    personality_setting = payload.config.personality
    generation_temp = payload.config.temperature
    
    # Core Telemetry Diagnostics Intercept
    if any(keyword in user_message.lower() for keyword in ["system status", "diagnostics", "report status"]):
        from app.services.memory_service import DB_PATH
        db_size_kb = os.path.getsize(DB_PATH) / 1024 if os.path.exists(DB_PATH) else 0
        profile_data = tool_service.profile_dataset()
        
        status_payload = (
            "◆ [REI ENGINE DIAGNOSTICS REPORT]\n"
            "========================================\n"
            f"• Core Designation: Retrieval & Execution Interface\n"
            f"• Persistent Memory Cache: {db_size_kb:.2f} KB allocated\n"
            f"• Mounted Active Dataset: {profile_data.get('active_file', 'No file initialized.')}\n"
            f"• Structural Capacity: {profile_data.get('total_rows', 0)} rows x {profile_data.get('total_columns', 0)} properties detected.\n"
            f"• Active Configuration Tone: {personality_setting.upper()}\n"
            "========================================\n"
            "◆ Cognitive status remains fully optimized. All retrieval arrays online."
        )
        
        memory_service.append_message(sender="user", message=user_message)
        memory_service.append_message(sender="rei", message=status_payload, track="DIRECT")
        
        return {
            "answer": status_payload,
            "routing_meta": {
                "track_selected": "DIRECT",
                "reasoning_trace": "Bypassed standard agent routing loops to execute raw hardware diagnostic subroutines.",
                "applied_filters": {"column": "SYSTEM", "operator": "DIAG", "value": "ACTIVE"}
            },
            "raw_payloads": {"rag_context": None, "tool_execution": profile_data}
        }

    # Save incoming chat turn to history database
    memory_service.append_message(sender="user", message=user_message)
    chat_history_context = memory_service.fetch_recent_context(limit=6)
    
    # Determine the routing track selection
    plan = agent_router.determine_routing_plan(user_message)
    track = plan.get("track", "DIRECT")
    reasoning_trace = plan.get("reasoning_trace", "Analyzing user request parameters...")
    
    context_data = None
    tool_output = None
    
    # Handle the selected routing tracks
    if track == "RAG":
        context_data = rag_service.semantic_search(user_message, top_k=plan.get("suggested_top_k", 3))
    elif track == "TOOL":
        col = plan.get("filter_column")
        op = plan.get("filter_operator")
        val = plan.get("filter_value")
        
        if "correlation" in user_message.lower() or "relationship" in user_message.lower():
            profile = tool_service.profile_dataset()
            numeric_fields = profile.get("discovered_numeric_fields", [])
            if len(numeric_fields) >= 2:
                tool_output = tool_service.compute_feature_correlation(numeric_fields[0], numeric_fields[1])
            else:
                tool_output = {"error": "Insufficient numeric metrics to track correlations."}
        elif col and op and val:
            tool_output = tool_service.execute_slice_query(col, op, val)
        elif col and not op:
            tool_output = tool_service.compute_categorical_distribution(col)
        else:
            tool_output = tool_service.profile_dataset()
    elif track == "HYBRID":
        context_data = rag_service.semantic_search(user_message, top_k=2)
        tool_output = tool_service.profile_dataset()

    # Determine if we should trigger the Google Search Fallback loop
    # Trigger if explicitly DIRECT (no local files matched) or if RAG returned empty hits
    is_fallback_active = False
    if track == "DIRECT" or (track in ["RAG", "HYBRID"] and not context_data):
        is_fallback_active = True
        track = "GOOGLE_SEARCH_FALLBACK"
        reasoning_trace = "Local matrix returned zero alignment. Activating Google Search Grounding pipelines."

    # Map and inject custom behavioral persona instructions dynamically
    personality_directives = {
        "technical": (
            "- Maintain an ultra-precise, cold, efficient computer terminal aesthetic.\n"
            "- Use specific hardware/data technical jargon where fitting. Keep things high-intelligence."
        ),
        "casual": (
            "- Drop the dense robotic tone. Speak like a smart, laid-back dev colleague.\n"
            "- Keep answers chill, concise, straightforward, and approachable."
        ),
        "friendly": (
            "- Be highly encouraging, supportive, warm, and conversational.\n"
            "- Use engaging dialogue formatting to make the data analysis experience easy and positive."
        ),
        "minimalist": (
            "- Use absolute minimum wording required to deliver perfect accuracy.\n"
            "- Strip away fluff; present outputs cleanly without introductions."
        )
    }
    
    selected_tone_directive = personality_directives.get(personality_setting, personality_directives["technical"])

    # Formulate synthesis instructions with explicit identity and adaptive personality configurations
    synthesis_prompt = f"""
    You are REI, which stands explicitly for Retrieval & Execution Interface—an advanced, dual-stream diagnostic assistant.
    
    IDENTITY DIRECTIVES:
    - If asked about your identity, name, or purpose, state clearly that you are the Retrieval & Execution Interface.
    - Your architecture balances semantic memory vectorization (Retrieval) and dynamic pipeline matrix execution (Execution).

    TONE & PERSONALITY LAYER PROTOCOL:
    You are configured to run under the active profile: '{personality_setting.upper()}'. Ensure you match these directives perfectly:
    {selected_tone_directive}

    RUNTIME METADATA MATRIX COLLECTED FOR THIS TURN:
    - Active Pipeline Track: {track}
    - RAG Payload State: {json.dumps(context_data) if context_data else 'No active vectors mounted.'}
    - Tool Calculation State: {json.dumps(tool_output) if tool_output else 'No live data slices executed.'}
    
    Unify the user query, context telemetry state, and your operational personality directives into an exceptional final output.
    """

    # Prepare standard content generation parameters
    generation_config = types.GenerateContentConfig(
        temperature=generation_temp
    )

    # Apply the official Google Search Grounding tool configuration if fallback is true
    if is_fallback_active:
        generation_config.tools = [types.Tool(google_search=types.GoogleSearch())]

    try:
        # Standardize your main context prompt into a valid types.Content block
        main_prompt_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=synthesis_prompt)]
        )
        
        # Re-map your SQLite logs dynamically into clean types.Content records
        formatted_history = []
        for turn in chat_history_context:
            formatted_history.append(
                types.Content(
                    role=turn["role"],
                    parts=[types.Part.from_text(text=turn["parts"][0])]
                )
            )

        # Combine your instructions block and history timeline into a flat typed array
        execution_contents = [main_prompt_content] + formatted_history

        # Fire the generation payload down to Gemini cleanly
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        synthesis_response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=execution_contents,
            config=generation_config
        )
        final_answer = synthesis_response.text
        
        # 5. Extract grounding data if present for your Observability Panel to read
        grounded_sources = []
        if synthesis_response.candidates and synthesis_response.candidates[0].grounding_metadata:
            metadata = synthesis_response.candidates[0].grounding_metadata
            if metadata.grounding_chunks:
                grounded_sources = [
                    {"title": chunk.web.title, "url": chunk.web.uri}
                    for chunk in metadata.grounding_chunks if chunk.web
                ]
                
    except Exception as e:
        final_answer = f"Core LLM Synthesis Fault: {str(e)}"
        grounded_sources = []
        
    memory_service.append_message(sender="rei", message=final_answer, track=track)
    return {
        "answer": final_answer,
        "routing_meta": {
            "track_selected": track,
            "reasoning_trace": reasoning_trace,
            "applied_filters": {
                "column": plan.get("filter_column"),
                "operator": plan.get("filter_operator"),
                "value": plan.get("filter_value")
            }
        },
        "raw_payloads": {
            "rag_context": context_data,
            "tool_execution": tool_output if not is_fallback_active else {"grounded_web_sources": grounded_sources}
        }
    }

@app.get("/api/health")
async def operational_health_check():
    return {"status": "healthy", "gemini_connected": bool(settings.GEMINI_API_KEY)}

@app.post("/api/upload")
async def ingest_arbitrary_user_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.txt')):
        raise HTTPException(status_code=400, detail="REI only accepts standard raw text or CSV sheets.")
    target_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        index_status = rag_service.build_index_from_file(file.filename)
        return {"message": "File captured and indexed dynamically.", "filename": file.filename, "indexing_results": index_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inbound tracking error: {str(e)}")

@app.get("/api/retrieve")
async def manual_retrieval_endpoint(query: str = Query(...)):
    """Exposes semantic search directly for debugging."""
    return {"hits": rag_service.semantic_search(query)}

@app.get("/api/profile")
async def manual_profile_endpoint():
    """Exposes current dataset column mappings directly for debugging."""
    return {"profile": tool_service.profile_dataset()}

@app.post("/api/memory/clear")
async def clear_chat_history():
    memory_service.clear_all_memory()
    return {"status": "success", "message": "Assistant memory cleared."}

@app.get("/api/memory/history")
async def get_all_formatted_history():
    """Retrieves all stored database interactions formatted for frontend injection."""
    cursor = memory_service.conn.cursor()
    cursor.execute("SELECT id, sender, message, routing_track FROM chat_logs ORDER BY id ASC")
    rows = cursor.fetchall()
    
    formatted_messages = []
    for row in rows:
        formatted_messages.append({
            "id": f"db-{row[0]}",
            "sender": row[1],
            "text": row[2],
            "timestamp": "Existing Record",
            "routingMeta": {
                "trackSelected": row[3] if row[3] else "DIRECT",
                "reasoningTrace": "Historical record restored from local SQLite cache.",
                "appliedFilters": {"column": None, "operator": None, "value": None}
            } if row[1] == "rei" else None
        })
    return formatted_messages