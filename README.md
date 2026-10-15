# TDMA Schedule Planner and Optimizer (5G/Tactical Private Networks)

## Overview
This repository contains a centralized **Schedule Planner and Optimizer (Brain)** designed for a Time Division Multiple Access (TDMA) wireless ad-hoc network, alongside an **EMANE Integration Bridge**. 

The solution addresses multi-hop interference and the hidden terminal problem in tactical communications by computing a conflict-free timeslot schedule and converting it into native EMANE XML schedule events.

---

## Features
- **Network Topology Graph**: Models radio nodes using `networkx` based on a configured 500-meter transmission coverage range.
- **Distance-2 Graph Coloring**: Prevents direct link (1-hop) and hidden-terminal (2-hop) collisions by ensuring adjacent and 2-hop neighbor nodes transmit in exclusive timeslots.
- **Spatial Reuse Optimization**: Applies a greedy graph-coloring heuristic (Degree-based coloring) to minimize overall frame length while enabling safe slot reuse across distant nodes (>2 hops).
- **EMANE Integration Bridge**: Automatically serializes slot assignments into an `emane-tdma-schedule` XML format for enforcement in EMANE simulation environments.

---

## Repository Structure
- `TDMA part 1&2.py` / `tdma_optimizer.py`: Complete Python script containing the graph analyzer, scheduler heuristic, CLI matrix generator, and XML bridge.
- `emane_tdma_schedule.xml`: Generated EMANE-compliant TDMA schedule file.
- `TDMA TOPOLOGY OPTIMIZATION REPORT.pdf`: Complete project documentation covering design process, math modeling, and final schedule matrices.

---

## How to Run

### Prerequisites
Install the required network analysis library:
```bash
pip install networkx
