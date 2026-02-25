"""
Deliberation module - handles agent disagreement and consensus building.
"""
from datetime import datetime
from typing import Optional
from agents.base_agent import AgentOutput


class DeliberationResult:
    def __init__(self, consensus: dict, disagreements: list[dict], final_confidence: float):
        self.consensus = consensus
        self.disagreements = disagreements
        self.final_confidence = final_confidence
        self.timestamp = datetime.utcnow()


def deliberate(outputs: list[AgentOutput]) -> DeliberationResult:
    """
    Given multiple agent outputs about the same entity,
    find consensus and surface disagreements.
    """
    if not outputs:
        return DeliberationResult({}, [], 0.0)

    if len(outputs) == 1:
        return DeliberationResult(
            outputs[0].data,
            [],
            outputs[0].confidence
        )

    # Find fields that all agents agree on vs disagree on
    all_keys = set()
    for output in outputs:
        all_keys.update(output.data.keys())

    consensus = {}
    disagreements = []

    for key in all_keys:
        values = [o.data.get(key) for o in outputs if key in o.data]
        if len(set(str(v) for v in values)) == 1:
            consensus[key] = values[0]
        else:
            disagreements.append({
                "field": key,
                "values": [
                    {"agent": o.agent_name, "value": o.data.get(key), "confidence": o.confidence}
                    for o in outputs if key in o.data
                ]
            })

    # Weighted average confidence
    total_weight = sum(o.confidence for o in outputs)
    final_confidence = total_weight / len(outputs) if outputs else 0.0

    return DeliberationResult(consensus, disagreements, final_confidence)
