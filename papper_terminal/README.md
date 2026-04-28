# 🦾 Papper Browser Agent (Level 1 Stable)

Papper is a high-performance, autonomous browser automation agent designed to evolve from a reactive tool into a proactive cognitive entity. Built for speed, precision, and industrial-grade stability.

## 🚀 Current Progress: Level 1 (The Body)
We have successfully implemented the core "Physical" layer of the agent, enabling robust interaction with any modern web application.

### Key Components:
- **`browser/controller.py`**: The central nervous system. Manages Playwright and CDP (Chrome DevTools Protocol) connections.
- **`browser/observer.py`**: The "Eye". Implements a high-speed Shadow DOM perception grid that assigns unique indices to interactive elements with O(1) deduplication.
- **`browser/actions.py`**: The "Muscle". Provides a suite of atomic interactions (Click, Type, Scroll, Key Press, Navigate) with built-in telemetry (automatic screenshots on failure).
- **`main.py`**: The interactive terminal interface for manual control and testing.

## 🛠️ Tech Stack
- **Engine**: Playwright (Chromium)
- **Perception**: Custom DOM-to-Grid Mapping
- **Logic**: Async Python 3.10+
- **Telemetry**: Rich logging & Automatic Screenshots

## 📂 Project Structure
```text
papper_terminal/
├── agent/       # Future Orchestrator
├── browser/     # Core Interaction Logic (Muscle & Eye)
├── planner/     # Future AI Cognitive Layer (Brain)
├── memory/      # Task Tracing & Loop Prevention
├── telemetry/   # Debug Screenshots & Logs
└── main.py      # Entry Point
```

## 🏁 Getting Started
1. **Install Dependencies**:
   ```bash
   pip install playwright pydantic python-dotenv
   playwright install chromium
   ```
2. **Run Manual Mode**:
   ```bash
   python main.py
   ```

## 🗺️ Roadmap
- [x] **Phase 1 (Level 1)**: Manual Interaction & Perception Grid.
- [ ] **Phase 2 (Level 2)**: Autonomous Brain (Ollama/Gemini Integration).
- [ ] **Phase 3 (Level 3)**: Human-in-the-loop & Emotional Intelligence.

---
*Created by Om Sawant & Antigravity AI*
