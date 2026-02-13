import re
import time
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..Utils.utils import LOG_DIR
from ..Browser.page_logger import log_page_html
from .selector_db import knowledge_db, save_knowledge
from .memory_manager import MemoryManager

class AIGOEngine:
    """Advanced AI operator for resolving complex interaction and extraction failures."""

    @staticmethod
    async def invoke_aigo(
        page: Any,
        context_key: str,
        element_key: str,
        failure_msg: str,
        objective: str = "Standard Interaction",
        expected_format: Optional[str] = None,
        heal_failure_count: int = 0,
        failure_heatmap: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        The Troubleshooting Expert V4.
        Implements failure heatmap analysis and intra-cycle redundancy.
        """
        print(f"    [AIGO V4] Initializing Expert with {heal_failure_count} failures and heatmap data...")
        
        timestamp = int(time.time())
        tag = f"AIGO_{context_key}_{timestamp}"
        await log_page_html(page, tag)
        
        PAGE_LOG_DIR = LOG_DIR / "Page"
        screenshot_files = list(PAGE_LOG_DIR.glob(f"*{tag}.png"))
        html_files = list(PAGE_LOG_DIR.glob(f"*{tag}.html"))
        
        if not screenshot_files or not html_files:
            return {"status": "error", "message": "Failed to capture artifacts for AIGO."}
            
        png_path = max(screenshot_files, key=os.path.getmtime)
        html_path = max(html_files, key=os.path.getmtime)
        
        with open(html_path, "r", encoding="utf-8") as f:
            raw_html = f.read()
            
        cleaned_html = re.sub(r"<script.*?</script>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
        cleaned_html = re.sub(r"<style.*?</style>", "", cleaned_html, flags=re.DOTALL | re.IGNORECASE)
        cleaned_html = cleaned_html[:80000] 
            
        image_data = {"mime_type": "image/png", "data": png_path.read_bytes()}
        heatmap_json = json.dumps(failure_heatmap, indent=2) if failure_heatmap else "None"

        prompt = f"""
        YOU ARE AN ELITE TROUBLESHOOTING EXPERT (V5). 
        Mission: Resolve a critical interaction failure with REDUNDANT and DIVERSE paths.

        ### MISSION CONTEXT
        - **Objective**: {objective}
        - **Target Element**: {element_key}
        - **Context**: {context_key}
        - **Failure Traceback**: {failure_msg}
        - **Phase 2 Failures**: {heal_failure_count} attempts failed.
        - **Failure Heatmap**: {heatmap_json}

        ### ASSETS
        - **Screenshot**: Visual state (Attached).
        - **HTML Source**: Sanitized structural state.
        - **Current Knowledge**: 
          {json.dumps(knowledge_db.get(context_key, {}), indent=2)}

        ### CRITICAL INSTRUCTIONS (V5)
        1. **HEATMAP ANALYSIS**: Study the Failure Heatmap carefully. Do NOT suggest selectors that appear in the heatmap UNLESS you provide a CLEAR MODIFICATION STRATEGY (e.g., parent element traversal, attribute-based selector, or sibling navigation).
        2. **PRIORITIZE HEATMAP AVOIDANCE**: Choose paths that circumvent the error patterns shown in the heatmap.
        3. **PATH DIVERSITY MANDATE**: Primary Path and Backup Path MUST be of DIFFERENT types:
           - If Primary is Path A (Selector), Backup must be Path B (Action Sequence) or Path C (Extraction).
           - If Primary is Path B, Backup must be Path A or Path C.
           - If Primary is Path C, Backup must be Path A or Path B.

        ### PATH DEFINITIONS
        - **Path A (Selector)**: A single robust CSS selector for direct interaction.
        - **Path B (Action Sequence)**: A series of preparatory steps (e.g., dismiss overlay, scroll) followed by a selector.
        - **Path C (Direct Extraction)**: Bypass UI entirely; extract data directly from HTML/screenshot.

        ### OUTPUT FORMAT (MANDATORY JSON)
        {{
            "diagnosis": "Heatmap analysis and failure explanation",
            "primary_path": {{
                "type": "A, B, or C",
                "healed_selector": "CSS selector if A or B",
                "recovery_steps": ["Step 1", "Step 2"] if B,
                "direct_extraction": "Data if C"
            }},
            "backup_path": {{
                "type": "MUST BE DIFFERENT FROM PRIMARY",
                "healed_selector": "CSS selector if A or B",
                "recovery_steps": ["Step 1"] if B,
                "direct_extraction": "Data if C"
            }},
            "is_resolution_complete": true
        }}
        """

        try:
            from .api_manager import gemini_api_call_with_rotation, GenerationConfig
            from .utils import clean_json_response
            
            response = await gemini_api_call_with_rotation(
                [prompt, image_data],
                generation_config=GenerationConfig(response_mime_type="application/json")
            )
            
            resolution = json.loads(clean_json_response(response.text))
            
            if resolution.get("is_resolution_complete"):
                # V5: Path Diversity Validation
                p_path = resolution.get("primary_path", {})
                b_path = resolution.get("backup_path", {})
                p_type = p_path.get("type", "A")
                b_type = b_path.get("type", "A")
                
                if p_type == b_type:
                    print(f"    [AIGO V5 WARNING] Path diversity violated. Primary={p_type}, Backup={b_type}. Forcing Backup to Path C.")
                    # Force backup to extraction as ultimate fallback
                    b_path["type"] = "C"
                    b_path["direct_extraction"] = f"FALLBACK: Extract '{element_key}' from HTML/screenshot"
                    resolution["backup_path"] = b_path
                
                # Memory persists the primary intent
                MemoryManager.store_memory(context_key, element_key, {
                    "action_type": f"AIGO_V5_{p_type}",
                    "selector": p_path.get("healed_selector"),
                    "diagnosis": resolution.get("diagnosis")
                })
                
                print(f"    [AIGO V5 SUCCESS] Paths: Primary={p_type}, Backup={b_type}. Diagnosis: {resolution.get('diagnosis')}")
                return resolution
            
            return {"status": "unresolved", "message": "Expert could not resolve even with redundancy."}

        except Exception as e:
            print(f"    [AIGO ERROR] Expert consultation failed: {e}")
            return {"status": "error", "message": str(e)}

        try:
            from .api_manager import gemini_api_call_with_rotation, GenerationConfig
            from .utils import clean_json_response
            
            response = await gemini_api_call_with_rotation(
                [prompt, image_data],
                generation_config=GenerationConfig(response_mime_type="application/json")
            )
            
            resolution = json.loads(clean_json_response(response.text))
            
            # 3. Handle Resolution
            if resolution.get("is_resolution_complete"):
                path = resolution.get("path_chosen", "A")
                new_sel = resolution.get("healed_selector")
                
                if (path in ["A", "B"]) and new_sel:
                    knowledge_db[context_key][element_key] = new_sel
                    save_knowledge()
                    
                # Record in Memory
                MemoryManager.store_memory(context_key, element_key, {
                    "action_type": f"AIGO_PATH_{path}",
                    "selector": new_sel,
                    "diagnosis": resolution.get("diagnosis"),
                    "extraction": resolution.get("direct_extraction")
                })
                
                print(f"    [AIGO SUCCESS] AI resolved via Path {path}: {resolution.get('diagnosis')}")
                return resolution
            
            return {"status": "unresolved", "message": "AI could not find a clear path."}

        except Exception as e:
            print(f"    [AIGO ERROR] AI Engine failure: {e}")
            return {"status": "error", "message": str(e)}
