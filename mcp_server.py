import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_FILE = Path(__file__).parent / "courses.json"

def load_courses() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

#helper functions

def search_course(query: str) -> dict:
    query = query.lower().strip()
    if not query:
        return {"error": "Query cannot be empty."}
    courses = load_courses()
    results = []
    for course in courses:
        searchable = " ".join([
            course["id"],
            course["name"],
            course["description"],
            " ".join(course["topics"]),
        ]).lower()
        if query in searchable:
            results.append({
                "id": course["id"],
                "name": course["name"],
                "instructor": course["instructor"],
                "credits": course["credits"],
                "schedule": course["schedule"],
                "description": course["description"],
            })
    if not results:
        return {"message": f"No courses found matching '{query}'.", "results": []}
    return {"results": results, "count": len(results)}


def get_course_details(course_id: str) -> dict:
    course_id = course_id.upper().strip()
    if not course_id:
        return {"error": "course_id cannot be empty."}
    courses = load_courses()
    for course in courses:
        if course["id"] == course_id:
            return course
    return {"error": f"Course '{course_id}' not found."}


def list_courses_by_topic(topic: str) -> dict:
    topic = topic.lower().strip()
    if not topic:
        return {"error": "Topic cannot be empty."}
    courses = load_courses()
    results = []
    for course in courses:
        if any(topic in t.lower() for t in course["topics"]):
            results.append({
                "id": course["id"],
                "name": course["name"],
                "topics": course["topics"],
                "prerequisites": course["prerequisites"],
            })
    if not results:
        return {"message": f"No courses cover the topic '{topic}'.", "results": []}
    return {"results": results, "count": len(results)}


def check_prerequisites(course_id: str) -> dict:
    course_id = course_id.upper().strip()
    if not course_id:
        return {"error": "course_id cannot be empty."}
    courses = load_courses()
    course_map = {c["id"]: c for c in courses}
    if course_id not in course_map:
        return {"error": f"Course '{course_id}' not found."}
    course = course_map[course_id]
    prereqs = course["prerequisites"]
    if not prereqs:
        return {"course_id": course_id, "course_name": course["name"], "prerequisites": [], "message": "No prerequisites required."}
    return {"course_id": course_id, "course_name": course["name"], "prerequisites": prereqs}


def suggest_next_courses(completed_ids: list[str]) -> dict:
    completed = {cid.upper().strip() for cid in completed_ids}
    if not completed:
        return {"error": "completed_courses list cannot be empty."}
    courses = load_courses()
    suggestions = []
    for course in courses:
        if course["id"] in completed:
            continue
        prereqs = set(course["prerequisites"])
        if prereqs.issubset(completed):
            suggestions.append({
                "id": course["id"],
                "name": course["name"],
                "credits": course["credits"],
                "description": course["description"],
            })
    if not suggestions:
        return {"message": "No new courses available based on completed courses.", "suggestions": []}
    return {"suggestions": suggestions, "count": len(suggestions)}

#server

mcp = FastMCP("course-assistant")


@mcp.tool()
def search_course_tool(query: str) -> str:
    """Search for courses by keyword. Matches against course ID, name, description, and topics."""
    return json.dumps(search_course(query), indent=2)


@mcp.tool()
def get_course_details_tool(course_id: str) -> str:
    """Get full details for a specific course by its course ID (e.g. CS4680)."""
    return json.dumps(get_course_details(course_id), indent=2)


@mcp.tool()
def list_courses_by_topic_tool(topic: str) -> str:
    """Find all courses that cover a given topic (e.g. RAG, regression, interpolation)."""
    return json.dumps(list_courses_by_topic(topic), indent=2)


@mcp.tool()
def check_prerequisites_tool(course_id: str) -> str:
    """Check what prerequisites are required before taking a course."""
    return json.dumps(check_prerequisites(course_id), indent=2)


@mcp.tool()
def suggest_next_courses_tool(completed_courses: list[str]) -> str:
    """Given a list of completed course IDs, suggest which courses you are now eligible to take."""
    return json.dumps(suggest_next_courses(completed_courses), indent=2)


#entry Point
if __name__ == "__main__":
    mcp.run()