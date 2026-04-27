"""
RecruiterPilot — WorkWeek IdeaIQ Integration Example

Prerequisites:
    pip install workweek-sdk  # or: pip install -e /path/to/workweek-sdk-python

API Key: wk_rpt_vMOl8QuINtve5tspDhWN7vCV8TCpSwfUXUFqZ2KWbPE
Team ID: eca3ac33-fcf9-4a00-bd28-4254f6066cb9  (RP Research)

Available templates:
    - candidate_dossier   — 13-section analyst-grade dossier (40 steps, 30 min)
    - market_analysis     — TAM/SAM/SOM, competitive landscape (60 steps, 30 min)
    - quick_lookup        — Fast factual answer (15 steps, 5 min)
"""

from workweek import WorkWeekClient

# --- Configuration ---
API_KEY = "wk_rpt_vMOl8QuINtve5tspDhWN7vCV8TCpSwfUXUFqZ2KWbPE"
BASE_URL = "https://gw.askvai.com"
RP_TEAM_ID = "eca3ac33-fcf9-4a00-bd28-4254f6066cb9"

client = WorkWeekClient(base_url=BASE_URL, api_key=API_KEY)


# --- Example 1: Candidate Dossier ---
def research_candidate(candidate_name: str, context: str = "") -> dict:
    """Submit a candidate dossier research task and wait for results."""
    query = f"Research candidate: {candidate_name}"
    if context:
        query += f". Context: {context}"
    query += ". Produce a comprehensive 13-section candidate dossier."

    result = client.execution.run_research(
        query=query,
        template_id="candidate_dossier",
        team_id=RP_TEAM_ID,
    )
    print(f"Submitted: {result['execution_id']}")

    # Wait for completion (polls every 15s, max 30 min)
    final = client.execution.wait_for_completion(
        result["execution_id"],
        poll_interval=15.0,
        timeout=1800.0,
    )
    print(f"Status: {final['status']}")

    if final["status"] == "completed":
        report = final.get("result", {})
        if isinstance(report, dict):
            print(f"Title: {report.get('title', 'N/A')}")
            print(f"Confidence: {report.get('confidence', 'N/A')}")
            print(f"Report length: {len(report.get('report', ''))} chars")
        return report
    else:
        print(f"Error: {final.get('error', 'Unknown')}")
        return final


# --- Example 2: Quick Lookup ---
def quick_lookup(question: str) -> dict:
    """Fast research for a simple question."""
    result = client.execution.run_research(
        query=question,
        template_id="quick_lookup",
        team_id=RP_TEAM_ID,
    )
    return client.execution.wait_for_completion(
        result["execution_id"],
        poll_interval=5.0,
        timeout=300.0,
    )


# --- Example 3: Custom research with instructions ---
def research_with_instructions(query: str, instructions: str) -> dict:
    """Research with custom instructions injected into the pipeline."""
    result = client.execution.run_research(
        query=query,
        template_id="candidate_dossier",
        team_id=RP_TEAM_ID,
        custom_instructions=instructions,
    )
    return client.execution.wait_for_completion(result["execution_id"])


if __name__ == "__main__":
    # Run a candidate dossier
    report = research_candidate(
        "Jensen Huang, CEO of NVIDIA",
        context="Evaluating for board advisory role. Focus on leadership style and strategic vision.",
    )
    if isinstance(report, dict) and "report" in report:
        # Save report to file
        with open("jensen_huang_dossier.md", "w") as f:
            f.write(report["report"])
        print(f"\nDossier saved to jensen_huang_dossier.md")
