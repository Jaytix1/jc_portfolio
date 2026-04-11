# FlakkOps — Operational Intelligence Dashboard

Built for my job as Operations Manager at Skechers USA to automate weekly shipment manifest processing, track hundreds of SKUs, detect new products before arrival, and surface AI-powered operational insights. Reduced manual data processing time by ~80%.

**Live Demo:** https://jc-portfolio-1.onrender.com

---

## The Problem

Every week, two truck shipments arrive with PDF manifests listing hundreds of SKUs and thousands of units. Reviewing them manually was time-consuming and error-prone — no visibility into new products before arrival, no historical trends, and no data-driven planning.

## The Solution

FlakkOps automates the entire workflow:

- **PDF Parsing** — upload manifests and automatically extract all SKUs, descriptions, quantities, and case packs
- **New Product Detection** — instantly flags products never received before so staff can prepare locations in advance
- **Task Automation** — auto-creates tasks when new products are detected, with priority levels tied to arrival dates
- **Analytics Dashboard** — top products by volume, YoY comparisons, and category breakdowns
- **AI Assistant** — powered by Claude API for intelligent manifest analysis and operational recommendations

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite |
| PDF Processing | pdfplumber |
| Data | Pandas |
| AI | Claude API (Anthropic) via FlakkAi integration |
| Deployment | Render |

## Local Setup

1. Navigate to the FlakkOps directory:
   ```bash
   cd FlakkOps
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   source venv/bin/activate      # Mac/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open http://localhost:5000

> **Note:** The AI assistant integrates with FlakkAi running on port 5002. Without it, the dashboard falls back to data-driven analysis automatically.
