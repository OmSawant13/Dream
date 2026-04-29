# 🦾 Papper Browser Agent (Level 2 Verified)

Papper is a high-performance, autonomous browser automation agent designed to evolve from a reactive tool into a proactive cognitive entity. Built for speed, precision, and industrial-grade stability.

---

## 🚀 Current Status: Level 2 (The Brain)
We have successfully transitioned from scripted actions to an **Autonomous Reasoning Agent**. Papper can now take high-level human goals and decompose them into multi-step browser interactions.

### **Verified Capabilities (Level 2):**
- **Autonomous Navigation**: Can move through multiple pages to reach a target.
- **Search & Filter**: Verified success on e-commerce (Flipkart) and news (BBC).
- **Multi-Step Logic**: Can find specific repositories on GitHub and navigate to sub-sections.
- **High-Speed Planning**: Integrated with **Groq (Llama 3.3 70B)** for sub-second thinking latency.

---

## 📊 Level Comparison

| Feature | **Level 1 (The Body)** | **Level 2 (The Brain)** | **Level 3 (The Intelligence)** |
| :--- | :--- | :--- | :--- |
| **Control** | Manual / Scripted | **Autonomous Reasoning** | Cognitive & Persistent |
| **Logic** | Single Action | **Multi-Step Planning** | Pattern Matching & Memory |
| **Perception** | Raw DOM Grid | **Semantic Understanding** | Data Extraction & Content Parsing |
| **State** | Blind execution | Basic Error Logs | **State Verification & Recovery** |

### ❌ What Level 2 Still CANNOT Do:
- **Remember Past Sessions**: Every task starts with a blank slate (no long-term memory).
- **Verify Success**: It assumes a click worked if the code didn't crash (no state validation).
- **Read Values**: It sees text but doesn't "understand" that ₹20,000 is less than ₹30,000.
- **Parallel Tasks**: Can only handle one tab/task at a time.
- **Extract Data**: Can navigate to info but cannot return it as a structured JSON/Report.

---

## 🏗️ Future Architecture: Level 3 (Cognitive Intelligence)
Level 3 focuses on **Deep Understanding** and **Data Extraction**. The agent will move beyond simple clicks to verify its own actions, remember past workflows across sessions, and return structured data (like price comparisons or order status) directly to the user.


---

## 📂 Project Structure
```text
repo_study/
├── agent/       # PapperAgent (Autonomous Orchestrator)
├── browser/     # Muscle & Eye (Actions & Perception Grid)
├── planner/     # Cognitive Layer (Groq/Llama Client)
├── memory/      # Session Tracking (Level 3 Expansion Point)
├── telemetry/   # Debug Screenshots & Logs
└── main.py      # Entry Point (Interactive & AI Mode)
```

## 🛠️ Setup
1. **Environment**: Copy `.env.example` to `.env` and add your `GROQ_API_KEY`.
2. **Dependencies**: `pip install -r requirements.txt`
3. **Run**: `python3 main.py ai "your task description"`

---
*Created by Om Sawant*
