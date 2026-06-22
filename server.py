import httpx
import os
from mcp.server.fastmcp import FastMCP

HEVY_API_KEY = os.environ.get("HEVY_API_KEY", "")
HEVY_BASE_URL = "https://api.hevyapp.com/v1"

mcp = FastMCP("Hevy MCP Server")

def hevy_get(endpoint: str, params: dict = {}):
    headers = {"api-key": HEVY_API_KEY}
    response = httpx.get(f"{HEVY_BASE_URL}{endpoint}", headers=headers, params=params)
    response.raise_for_status()
    return response.json()

@mcp.tool()
def get_recent_workouts(count: int = 5) -> str:
    """Get the most recent workouts from Hevy."""
    data = hevy_get("/workouts", {"page": 1, "pageSize": count})
    workouts = data.get("workouts", [])
    if not workouts:
        return "No workouts found."
    result = []
    for w in workouts:
        name = w.get("name", "Unnamed")
        date = w.get("start_time", "")[:10]
        exercises = w.get("exercises", [])
        exercise_names = [e.get("title", "") for e in exercises]
        result.append(f"{date} — {name}: {', '.join(exercise_names)}")
    return "\n".join(result)

@mcp.tool()
def get_workout_detail(workout_id: str) -> str:
    """Get full details of a specific workout including sets and reps."""
    data = hevy_get(f"/workouts/{workout_id}")
    workout = data.get("workout", {})
    name = workout.get("name", "Unnamed")
    date = workout.get("start_time", "")[:10]
    exercises = workout.get("exercises", [])
    result = [f"Workout: {name} ({date})"]
    for ex in exercises:
        title = ex.get("title", "")
        sets = ex.get("sets", [])
        set_details = []
        for s in sets:
            reps = s.get("reps", "?")
            weight = s.get("weight_kg", "?")
            set_details.append(f"{reps} reps @ {weight}kg")
        result.append(f"  {title}: {', '.join(set_details)}")
    return "\n".join(result)

@mcp.tool()
def get_exercise_history(exercise_name: str) -> str:
    """Get history for a specific exercise to track progressive overload."""
    data = hevy_get("/workouts", {"page": 1, "pageSize": 20})
    workouts = data.get("workouts", [])
    history = []
    for w in workouts:
        date = w.get("start_time", "")[:10]
        for ex in w.get("exercises", []):
            if exercise_name.lower() in ex.get("title", "").lower():
                sets = ex.get("sets", [])
                best_set = max(sets, key=lambda s: s.get("weight_kg", 0), default={})
                weight = best_set.get("weight_kg", "?")
                reps = best_set.get("reps", "?")
                history.append(f"{date}: best set {reps} reps @ {weight}kg")
    if not history:
        return f"No history found for '{exercise_name}'."
    return "\n".join(history)

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
