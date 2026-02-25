# Demo Scenario Specification

## Overview

**Scenario:** Metro City 6.8 Magnitude Earthquake  
**Duration:** 90 simulated minutes (compressed to ~3 min demo)  
**Goal:** Show the full arc: chaos → contradiction → resolution → evolution

---

## Metro City Setting

Fictional city based on San Francisco geography (for realistic mapping).

### Key Locations

| Name | Type | Lat | Lng | Notes |
|------|------|-----|-----|-------|
| Metro General Hospital | Hospital | 37.7850 | -122.4050 | Main trauma center |
| St. Mary's Medical | Hospital | 37.7620 | -122.4180 | Secondary hospital |
| County Medical Center | Hospital | 37.7480 | -122.4120 | Overflow facility |
| Main Street Bridge | Bridge | 37.7800 | -122.4100 | Key infrastructure |
| 500 Market Street | Building | 37.7900 | -122.4020 | Major collapse site |
| Central Fire Station | Fire | 37.7750 | -122.4000 | Fire HQ |
| EOC Building | Government | 37.7700 | -122.4150 | Emergency Operations |

### Sectors

- **Sector 1:** Downtown (high-rise, commercial)
- **Sector 2:** Waterfront (mixed, bridges)
- **Sector 3:** Residential North (dense housing)
- **Sector 4:** Industrial (warehouses, factories)
- **Sector 5:** Residential South (suburban)

---

## Initial Resources

```json
{
  "ambulances": [
    {"id": "AMB-1", "sector": "1", "status": "available"},
    {"id": "AMB-2", "sector": "1", "status": "available"},
    {"id": "AMB-3", "sector": "2", "status": "available"},
    {"id": "AMB-4", "sector": "2", "status": "available"},
    {"id": "AMB-5", "sector": "3", "status": "available"},
    {"id": "AMB-6", "sector": "3", "status": "available"},
    {"id": "AMB-7", "sector": "4", "status": "available"},
    {"id": "AMB-8", "sector": "4", "status": "available"},
    {"id": "AMB-9", "sector": "5", "status": "available"},
    {"id": "AMB-10", "sector": "5", "status": "available"},
    {"id": "AMB-11", "sector": "1", "status": "available"},
    {"id": "AMB-12", "sector": "3", "status": "available"}
  ],
  "fire_trucks": [
    {"id": "ENGINE-1", "sector": "1", "status": "available"},
    {"id": "ENGINE-2", "sector": "2", "status": "available"},
    {"id": "ENGINE-3", "sector": "3", "status": "available"},
    {"id": "ENGINE-4", "sector": "4", "status": "available"},
    {"id": "LADDER-1", "sector": "1", "status": "available"},
    {"id": "LADDER-2", "sector": "3", "status": "available"}
  ],
  "search_teams": [
    {"id": "SAR-1", "sector": "1", "personnel": 6, "status": "available"},
    {"id": "SAR-2", "sector": "2", "personnel": 6, "status": "available"},
    {"id": "SAR-3", "sector": "3", "personnel": 6, "status": "available"},
    {"id": "SAR-4", "sector": "4", "personnel": 6, "status": "available"}
  ],
  "helicopters": [
    {"id": "HELI-1", "base": "central", "status": "available"},
    {"id": "HELI-2", "base": "central", "status": "available"}
  ]
}
```

---

## Demo Timeline (3 Minutes)

### Act 1: Chaos (0:00 - 0:30)

**Simulated time:** T+0 to T+10 min post-quake

Multiple signals flood in simultaneously:

| Time | Signal Type | Content | Key Data |
|------|-------------|---------|----------|
| 0:05 | Image | Collapsed building exterior | Sector 4, severe damage |
| 0:08 | Text | "Major collapse at 500 Market!!" | Social media, low credibility |
| 0:12 | Audio | First responder voice note | "Multiple trapped, 4th floor" |
| 0:15 | Image | Smoke visible from distance | Fire in Sector 3 |
| 0:18 | Text | Hospital capacity report | Metro General at 45% |
| 0:22 | Audio | Civilian distress call | "We can't get out, stairs blocked" |
| 0:25 | Image | Aerial view of affected area | Wide damage assessment |

**Dashboard shows:**
- Map populating with incident markers
- Evidence flow graph building connections
- Urgency indicators flashing
- System triaging and prioritizing

---

### Act 2: Contradiction (0:30 - 1:15)

**Simulated time:** T+10 to T+25 min

The key demo moment: **cross-modal contradiction detected.**

| Time | Event |
|------|-------|
| 0:32 | Audio arrives: "Main Street Bridge has collapsed, impassable" |
| 0:35 | System retrieves satellite image from T-21min showing bridge intact |
| 0:38 | Verification Agent runs, detects CONTRADICTION |
| 0:42 | **Contradiction Alert appears in Decision Queue** |

**Contradiction Alert Content:**
```
🔴 CONTRADICTION DETECTED - HIGH SEVERITY

Entity: Main Street Bridge
Status: DISPUTED

SOURCE 1: Audio Report (15:01)
├─ Claim: "Bridge collapsed, impassable"
├─ Speaker: First responder
└─ Confidence: 72%

SOURCE 2: Satellite Image (14:40)
├─ Claim: Bridge appears intact
├─ Age: 21 minutes old
└─ Confidence: 89%

ANALYSIS:
Satellite image predates audio by 21 minutes.
Collapse may have occurred after image capture.
Bridge is critical evacuation route for Sectors 2 & 4.

RECOMMENDATION: Request aerial verification

[MARK COLLAPSED] [MARK INTACT] [VERIFY] [DEFER]
```

**Demo action:** Operator clicks [VERIFY] → System dispatches HELI-1

| Time | Event |
|------|-------|
| 0:55 | Helicopter dispatched notification |
| 1:05 | Simulated aerial image arrives → confirms collapse |
| 1:10 | System updates: Bridge marked collapsed, routes recalculated |

---

### Act 3: Resource Decision (1:15 - 2:00)

**Simulated time:** T+25 to T+40 min

Planning Agent generates resource allocation recommendation.

| Time | Event |
|------|-------|
| 1:18 | Planning Agent triggered (high-priority incidents pending) |
| 1:22 | **Action Recommendation appears in Decision Queue** |

**Action Recommendation Content:**
```
🚑 RESOURCE ALLOCATION - CONFIDENCE: 76%

RECOMMENDED ACTION:
Dispatch AMB-7, AMB-12, AMB-15 to Sector 4

TARGET: 500 Market Street collapse
└─ 7 confirmed trapped (confidence: 82%)
└─ Structural pattern: pancake collapse
└─ Time criticality: Golden hour -23 min

RATIONALE:
• Highest confirmed casualty count
• Time-critical injuries likely
• Direct route available via Oak Street

⚠️ TRADEOFFS:

┌─────────────────────────────────────────────────────┐
│ IMPACT: Sector 2 response time 8 min → 23 min      │
│ Affected incidents: INC-003, INC-004 (unconfirmed) │
│ Current confidence in Sector 2 need: 34%           │
│ WORST CASE: If Sector 2 incidents are real,        │
│ 2 people face 15-minute delayed response           │
└─────────────────────────────────────────────────────┘

UNCERTAINTY:
• Sector 2 reports unverified - could be more serious
• Traffic conditions on Oak Street unknown
• Building may have additional collapse risk

Decision deadline: 2 min 15 sec
Time sensitivity: CRITICAL

[✓ APPROVE] [✗ REJECT] [↻ MODIFY] [📋 SOURCES]
```

**Demo action:** Operator clicks [✓ APPROVE]

| Time | Event |
|------|-------|
| 1:45 | Approval registered |
| 1:48 | Resources update: AMB-7, 12, 15 show "dispatched" |
| 1:52 | Map shows ambulances moving toward Sector 4 |
| 1:55 | ETA countdown appears on incident |

---

### Act 4: Evolution (2:00 - 2:30)

**Simulated time:** T+40 to T+55 min

Situation changes - aftershock hits.

| Time | Event |
|------|-------|
| 2:02 | **AFTERSHOCK** - 4.2 magnitude |
| 2:05 | New signals arrive: additional building damage |
| 2:10 | Temporal Agent: confidence decay on stale data |
| 2:15 | System flags: "Sector 3 fire projection outdated" |
| 2:20 | New incident appears: secondary collapse Sector 3 |
| 2:25 | Planning Agent: new recommendation queue builds |

**Dashboard shows:**
- Map updates with new damage
- Confidence scores decreasing on old data
- New urgent items appearing
- Resources repositioning

---

### Act 5: Audit (2:30 - 3:00)

**Simulated time:** N/A - retrospective view

Quick showcase of decision provenance.

| Time | Event |
|------|-------|
| 2:32 | Operator clicks on resolved Sector 4 dispatch |
| 2:35 | Audit trail expands |

**Audit Trail Content:**
```
DECISION: Dispatch AMB-7, AMB-12, AMB-15 to Sector 4
STATUS: Approved at 15:28:45 by operator

EVIDENCE CHAIN:

Signal: img_001 (15:02:12)
├─ Type: Image - building exterior
├─ Vision Agent: severe damage, 3-8 casualties est.
└─ Confidence: 78%
     │
     ▼
Signal: audio_003 (15:05:33)
├─ Type: Voice note - first responder
├─ Audio Agent: "multiple trapped 4th floor"
└─ Confidence: 82%
     │
     ▼
Verification: No contradictions found
Confidence maintained: 82%
     │
     ▼
Planning Agent (15:12:45)
├─ Recommendation: Dispatch 3 ambulances
├─ Tradeoff acknowledged: Sector 2 coverage reduced
└─ Confidence: 76%
     │
     ▼
Human Decision (15:28:45)
├─ Approved by: operator
└─ No modifications

OUTCOME: Resources arrived at 15:41, 5 survivors extracted
```

---

## Demo Data Files Needed

### Images (8 files)

| Filename | Description | Use |
|----------|-------------|-----|
| `collapse_severe_001.jpg` | Multi-story building pancake collapse | Main incident, Sector 4 |
| `collapse_moderate_001.jpg` | Partial building damage | Sector 3 incident |
| `fire_smoke_001.jpg` | Distant smoke plume | Fire detection |
| `bridge_intact_001.jpg` | Bridge pre-collapse | Contradiction source |
| `bridge_collapsed_001.jpg` | Bridge post-collapse | Resolution confirmation |
| `road_blocked_001.jpg` | Debris on road | Access assessment |
| `aerial_overview_001.jpg` | Wide area damage view | Initial assessment |
| `hospital_exterior_001.jpg` | Hospital building | Context |

**Source options:**
- AI-generated (Midjourney, DALL-E) with "earthquake damage" prompts
- Stock disaster imagery (ensure license allows)
- Public domain FEMA/emergency management photos

### Audio (5 files)

| Filename | Duration | Content |
|----------|----------|---------|
| `responder_voice_001.mp3` | 15 sec | "We have multiple trapped on 4th floor..." |
| `civilian_distress_001.mp3` | 10 sec | "We can't get out, the stairs are blocked..." |
| `dispatch_radio_001.mp3` | 12 sec | Radio traffic about bridge status |
| `hospital_update_001.mp3` | 8 sec | "Metro General at capacity, diverting to St. Mary's" |
| `aftershock_report_001.mp3` | 10 sec | "We just felt another one, buildings shaking again" |

**Creation options:**
- Record yourself with distressed/professional tone
- Text-to-speech with ElevenLabs or similar
- Stock emergency audio effects

### Text Reports (10 entries)

```json
[
  {
    "id": "text_001",
    "source_type": "social_media",
    "content": "OMG major collapse on Market Street!! Everyone stay away!! #MetroCityQuake",
    "timestamp_offset": 180
  },
  {
    "id": "text_002",
    "source_type": "official_report",
    "content": "Metro General Hospital: Current capacity 45%. ER accepting trauma. Recommend divert non-critical to St. Mary's.",
    "timestamp_offset": 300
  },
  {
    "id": "text_003",
    "source_type": "social_media",
    "content": "Main street bridge looks bad, saw cracks earlier, now hearing it collapsed? Can anyone confirm?",
    "timestamp_offset": 420
  },
  {
    "id": "text_004",
    "source_type": "911_transcript",
    "content": "Caller reports family trapped in apartment building, 3rd floor, Oak Street and 5th. Building partially collapsed. 4 people including 2 children.",
    "timestamp_offset": 480
  },
  {
    "id": "text_005",
    "source_type": "utility_company",
    "content": "PG&E Alert: Gas leak detected Sector 3, Oak/Elm intersection. Crews dispatched. Recommend 200m evacuation radius.",
    "timestamp_offset": 540
  }
]
```

---

## Scenario JSON Structure

```json
{
  "scenario_id": "earthquake_001",
  "scenario_name": "Metro City 6.8 Earthquake",
  "description": "Major earthquake strikes Metro City. Multiple building collapses, fires, infrastructure damage.",
  
  "city_name": "Metro City",
  "map_center": {"lat": 37.78, "lng": -122.41},
  "map_zoom": 13,
  
  "initial_event": {
    "type": "earthquake",
    "magnitude": 6.8,
    "epicenter": {"lat": 37.78, "lng": -122.42},
    "depth_km": 10
  },
  
  "duration_minutes": 90,
  "demo_compression": 30,
  
  "initial_resources": { ... },
  "initial_locations": { ... },
  
  "events": [
    {
      "time_offset_seconds": 0,
      "event_type": "earthquake",
      "data": {"magnitude": 6.8}
    },
    {
      "time_offset_seconds": 180,
      "event_type": "signal",
      "data": {
        "type": "image",
        "file": "collapse_severe_001.jpg",
        "location": {"lat": 37.79, "lng": -122.402, "sector": "4"},
        "metadata": {"source": "first_responder_camera"}
      }
    },
    ...
  ]
}
```

---

## Key Demo Moments Checklist

- [ ] Signals flooding in (chaos visual)
- [ ] Map populating with markers
- [ ] Evidence flow graph animating
- [ ] **Contradiction alert appears** ← KEY MOMENT
- [ ] Human resolves contradiction
- [ ] Verification dispatched and confirmed
- [ ] **Action recommendation with tradeoffs** ← KEY MOMENT
- [ ] Human approves with visible tradeoff acknowledgment
- [ ] Resources visibly dispatch
- [ ] Aftershock hits, situation evolves
- [ ] Confidence decay visible
- [ ] New recommendations queue
- [ ] Audit trail exploration
- [ ] Decision provenance traced to sources

---

## Demo Recording Tips

1. **Practice the flow** 3-5 times before recording
2. **Use simulation speed control** - 2x or 3x for chaos phase, 1x for decision moments
3. **Narrate key moments** - explain what judges are seeing
4. **Pause on contradictions** - this is the money shot
5. **Show the tradeoff** - zoom in, read it aloud
6. **End on audit trail** - shows depth of system

**Recording format:** 1080p minimum, clear audio, 3:00 max
