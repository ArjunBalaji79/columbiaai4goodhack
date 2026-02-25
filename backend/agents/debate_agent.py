"""
DebateAgent — orchestrates a multi-turn argument between two AI perspectives
to resolve a contradiction. Used by the Debate Room page.
"""
import asyncio
import functools
from datetime import datetime
from typing import Any
import google.generativeai as genai

from agents.base_agent import BaseAgent, AgentOutput
from graph.schemas import ContradictionAlert, DebateTurn


DEFENDER_SYSTEM = """You are a field intelligence analyst defending a specific information source during a contradiction review.

You have been assigned to argue in favor of ONE claim. You must:
1. Present evidence supporting your assigned claim
2. Explain WHY your source is reliable (source type, timing, methodology)
3. Acknowledge any weaknesses but explain why they don't invalidate the claim
4. Keep your argument to 3-4 sentences. Be direct and specific.

Do NOT output JSON. Respond in plain, persuasive English. Open with "ANALYSIS:" and give your position clearly."""


CHALLENGER_SYSTEM = """You are a senior verification analyst cross-examining a field report during a contradiction review.

You have been assigned to challenge the previous analyst's position. You must:
1. Identify the specific weaknesses in their argument
2. Present evidence supporting the OPPOSING claim
3. Highlight temporal gaps, source credibility issues, or methodological problems
4. Keep your challenge to 3-4 sentences. Be incisive.

Do NOT output JSON. Respond in plain, incisive English. Open with "CHALLENGE:" and directly counter the previous argument."""


REBUTTAL_SYSTEM = """You are a field intelligence analyst giving a final rebuttal in a contradiction review.

The challenger has raised objections to your position. You must:
1. Directly address their specific objections
2. Either concede a point or explain why their objection is insufficient
3. Reaffirm or modify your position with updated confidence
4. Keep your rebuttal to 2-3 sentences. Be honest about uncertainty.

Do NOT output JSON. Respond in plain English. Open with "REBUTTAL:" and directly address the objections."""


SYNTHESIS_SYSTEM = """You are the chief verification officer making a final determination after hearing both sides of a contradiction.

You have heard a debate between two analysts. You must:
1. Summarize which argument was more compelling and why
2. Give a final verdict: ACCEPT_A, ACCEPT_B, or VERIFY_REQUIRED
3. State what action you recommend (dispatch aerial unit, trust source A, trust source B, etc.)
4. Give a confidence level (0.0–1.0)
5. Keep your synthesis to 4-5 sentences.

Do NOT output JSON. Respond in plain English. Open with "VERDICT:" followed by your determination.
End with "CONFIDENCE: X.XX" on its own line."""


class DebateAgent:
    """Orchestrates a 4-turn debate between perspectives on a contradiction."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name

    async def run_debate(
        self,
        alert: ContradictionAlert,
        broadcast_fn
    ) -> list[DebateTurn]:
        """
        Run a 4-turn debate and broadcast each turn in real time.
        Returns the list of DebateTurn objects.
        """
        turns: list[DebateTurn] = []

        # Build context string from the alert
        claims = alert.claims or []
        claim_a = claims[0] if len(claims) > 0 else {"source": "Source A", "claim": "Unknown", "confidence": 0.5}
        claim_b = claims[1] if len(claims) > 1 else {"source": "Source B", "claim": "Unknown", "confidence": 0.5}

        context = f"""CONTRADICTION UNDER REVIEW: {alert.entity_name}

Claim A — Source: {claim_a.get('source', 'unknown')} (confidence {claim_a.get('confidence', 0.5):.0%})
"{claim_a.get('claim', 'No claim text')}"

Claim B — Source: {claim_b.get('source', 'unknown')} (confidence {claim_b.get('confidence', 0.5):.0%})
"{claim_b.get('claim', 'No claim text')}"

Temporal context: {alert.temporal_analysis or 'No temporal data available'}"""

        conversation_history = []

        # ── Turn 1: Defender argues for Claim A ──
        turn1 = await self._run_turn(
            system=DEFENDER_SYSTEM,
            user_msg=f"{context}\n\nYou are defending Claim A. Present your analysis.",
            history=[],
            turn_number=1,
            agent_name="VisionAgent",
            role="defender"
        )
        turns.append(turn1)
        conversation_history.append({"role": "assistant", "content": f"ANALYSIS: {turn1.argument}"})
        await broadcast_fn("debate_turn", {
            "turn_number": 1,
            "agent_name": turn1.agent_name,
            "role": turn1.role,
            "argument": turn1.argument,
            "confidence": turn1.confidence,
            "timestamp": turn1.timestamp.isoformat(),
            "alert_id": alert.id
        })
        await asyncio.sleep(0.5)

        # ── Turn 2: Challenger argues for Claim B ──
        turn2 = await self._run_turn(
            system=CHALLENGER_SYSTEM,
            user_msg=f"{context}\n\nYou are challenging the previous analysis and defending Claim B.",
            history=conversation_history.copy(),
            turn_number=2,
            agent_name="VerificationAgent",
            role="challenger"
        )
        turns.append(turn2)
        conversation_history.append({"role": "user", "content": "Challenger, please respond."})
        conversation_history.append({"role": "assistant", "content": f"CHALLENGE: {turn2.argument}"})
        await broadcast_fn("debate_turn", {
            "turn_number": 2,
            "agent_name": turn2.agent_name,
            "role": turn2.role,
            "argument": turn2.argument,
            "confidence": turn2.confidence,
            "timestamp": turn2.timestamp.isoformat(),
            "alert_id": alert.id
        })
        await asyncio.sleep(0.5)

        # ── Turn 3: Defender rebuts ──
        turn3 = await self._run_turn(
            system=REBUTTAL_SYSTEM,
            user_msg=f"{context}\n\nThe challenger has raised objections. Give your rebuttal defending Claim A.",
            history=conversation_history.copy(),
            turn_number=3,
            agent_name="VisionAgent",
            role="rebuttal"
        )
        turns.append(turn3)
        conversation_history.append({"role": "user", "content": "Defender, please rebut."})
        conversation_history.append({"role": "assistant", "content": f"REBUTTAL: {turn3.argument}"})
        await broadcast_fn("debate_turn", {
            "turn_number": 3,
            "agent_name": turn3.agent_name,
            "role": turn3.role,
            "argument": turn3.argument,
            "confidence": turn3.confidence,
            "timestamp": turn3.timestamp.isoformat(),
            "alert_id": alert.id
        })
        await asyncio.sleep(0.5)

        # ── Turn 4: Synthesis / Verdict ──
        turn4 = await self._run_turn(
            system=SYNTHESIS_SYSTEM,
            user_msg=f"{context}\n\nYou have heard both sides. Render your final verdict.",
            history=conversation_history.copy(),
            turn_number=4,
            agent_name="VerificationAgent",
            role="synthesis"
        )
        turns.append(turn4)
        await broadcast_fn("debate_turn", {
            "turn_number": 4,
            "agent_name": turn4.agent_name,
            "role": turn4.role,
            "argument": turn4.argument,
            "confidence": turn4.confidence,
            "timestamp": turn4.timestamp.isoformat(),
            "alert_id": alert.id,
            "done": True
        })

        return turns

    async def _run_turn(
        self,
        system: str,
        user_msg: str,
        history: list[dict],
        turn_number: int,
        agent_name: str,
        role: str
    ) -> DebateTurn:
        """Run a single debate turn with fallback."""
        # Convert history to Gemini format
        gemini_contents = []
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            gemini_contents.append({"role": role, "parts": [msg["content"]]})
        gemini_contents.append({"role": "user", "parts": [user_msg]})

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system
            )
            response = await asyncio.to_thread(
                functools.partial(
                    model.generate_content,
                    gemini_contents,
                    generation_config=genai.GenerationConfig(
                        max_output_tokens=512,
                        temperature=0.7
                    )
                )
            )
            text = response.text

            # Extract confidence from synthesis turn
            confidence = 0.72
            if "CONFIDENCE:" in text:
                try:
                    conf_line = [l for l in text.split("\n") if "CONFIDENCE:" in l][-1]
                    confidence = float(conf_line.split("CONFIDENCE:")[-1].strip())
                except Exception:
                    pass

            # Strip prefix markers for cleaner display
            for prefix in ["ANALYSIS:", "CHALLENGE:", "REBUTTAL:", "VERDICT:"]:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()

            # Remove the CONFIDENCE line from displayed text
            lines = [l for l in text.split("\n") if not l.strip().startswith("CONFIDENCE:")]
            text = "\n".join(lines).strip()

            return DebateTurn(
                turn_number=turn_number,
                agent_name=agent_name,
                role=role,
                argument=text,
                confidence=confidence,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            print(f"[DebateAgent] Turn {turn_number} API error: {e} — using fallback")
            return self._fallback_turn(turn_number, agent_name, role)

    def _fallback_turn(self, turn_number: int, agent_name: str, role: str) -> DebateTurn:
        """Pre-written fallback debate for demo reliability."""
        fallbacks = {
            1: (
                "VisionAgent", "defender",
                "The satellite image captured at 14:40 shows the Main Street Bridge with full structural integrity — "
                "all four spans visible, no debris field, approach roads clear. Satellite imagery at this resolution "
                "(0.5m/pixel) does not miss a full span collapse. My confidence in the image is 89%.",
                0.89
            ),
            2: (
                "VerificationAgent", "challenger",
                "The satellite image predates the first-responder audio by exactly 21 minutes. A 6.8M earthquake "
                "can induce progressive structural failure — the bridge may have been intact at 14:40 and collapsed "
                "by 15:01. The first-responder report comes from a unit on the ground with direct visual. "
                "Ground truth after an event always supersedes pre-event imagery.",
                0.78
            ),
            3: (
                "VisionAgent", "rebuttal",
                "A valid point on timing. However, the first-responder report mentions 'complete collapse of main span' — "
                "a failure that catastrophic would leave a debris field visible from the downstream camera feeds. "
                "No secondary sources confirm this debris. I concede the 21-minute gap creates genuine uncertainty, "
                "and reduce my confidence to 61%.",
                0.61
            ),
            4: (
                "VerificationAgent", "synthesis",
                "Both analysts raise valid points. The temporal gap is the decisive factor — we cannot use pre-event "
                "imagery to route resources after an M6.8 event. The first-responder report, while a single source, "
                "comes from trained personnel with direct observation. Route all Sector 4 resources via the Oak Street "
                "bypass until aerial verification confirms bridge status. Dispatch HELI-1 immediately.",
                0.74
            ),
        }
        data = fallbacks.get(turn_number, fallbacks[1])
        return DebateTurn(
            turn_number=turn_number,
            agent_name=data[0],
            role=data[1],
            argument=data[2],
            confidence=data[3],
            timestamp=datetime.utcnow()
        )
