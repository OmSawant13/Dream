# 🦾 Papper Browser Agent (Level 3: Cognitive Intelligence)

Papper is a high-performance, autonomous browser automation agent designed to evolve from a reactive tool into a proactive cognitive entity. Built for speed, precision, and industrial-grade stability.

---

## 🚀 Current Status: Level 3 (Memory & Persistence)
We have successfully integrated **Phase E: Persistent Memory**, moving Papper from an ephemeral execution model to a learning system. The agent now has a long-term "brain" backed by SQLite, allowing it to remember past successes and failures across sessions.

### **Verified Capabilities (Level 3 - Phase E):**
- **Persistent Memory Engine**: SQLite-backed storage for all workflows, actions, and browser states.
- **State Hashing & Loop Detection**: Uses dual Visual + Text hashing to detect and abort infinite execution loops.
- **Case-Based Reasoning (CBR)**: Automatically retrieves and learns from similar past successful tasks to improve planning.
- **OpenRouter/Groq Dual Support**: Native integration with multiple LLM providers for sub-second reasoning latency.
- **Failure Signatures**: Can identify "dead-ends" by recognizing state+action combinations that failed in previous runs.

---

## 📊 Level Comparison

| Feature | **Level 1 (The Body)** | **Level 2 (The Brain)** | **Level 3 (The Intelligence)** |
| :--- | :--- | :--- | :--- |
| **Control** | Manual / Scripted | Autonomous Reasoning | **Persistent Autonomy** |
| **Memory** | None | Session-only (RAM) | **Cross-Session (SQLite)** |
| **Loop Resilience** | None | Basic (Stuck logs) | **Visual + Text Hashing** |
| **Learning** | None | None | **Case-Based Reasoning (CBR)** |
| **State** | Blind execution | Basic Error Logs | **State Verification & Recovery** |

### ❌ Remaining Challenges (Phase F & Beyond):
- **Verification Logic**: Distinguishing between "Progress" and "Visual-only" changes (Upcoming in Phase F).
- **Complex Data Extraction**: Returning structured JSON reports from multi-page research.
- **Advanced Blocker Bypass**: Heuristic-based handling of complex bot-detection and popups.

---

## 🏗️ Future Architecture: Phase F (State Verification)
Next in line is **Phase F**, which will implement deep state verification logic. This will allow the agent to understand *why* an action failed and escapse loops by choosing a fundamentally different approach instead of just aborting.

---

## 📂 Project Structure
```text
repo_study/
├── agent/       # PapperAgent (Autonomous Orchestrator)
├── browser/     # Muscle & Eye (Actions & Perception Grid)
├── memory/      # Persistent Memory Engine (SQLite / TF-IDF logic)
├── planner/     # Cognitive Layer (OpenRouter/Groq Client)
├── research/    # Phase-wise architectural findings
├── telemetry/   # Debug Screenshots & Logs
└── main.py      # Entry Point (Interactive & AI Mode)
```

## 🛠️ Setup
1. **Environment**: Copy `.env.example` to `.env`.
2. **Provider**: Set `LLM_PROVIDER=openrouter` and `LLM_MODEL` in your `.env`.
3. **Dependencies**: `pip install -r requirements.txt`
4. **Run**: `python3 main.py ai "your task description"`

---
*Developed with ❤️ by Om Sawant*
