import json
import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

#Data
DATA_FILE = Path(__file__).parent / "courses.json"

def load_courses() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

#Tool Helpers

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
        return {
            "course_id": course_id,
            "course_name": course["name"],
            "prerequisites": [],
            "message": "No prerequisites required.",
        }

    prereq_details = []
    for pid in prereqs:
        if pid in course_map:
            prereq_details.append({
                "id": pid,
                "name": course_map[pid]["name"],
                "credits": course_map[pid]["credits"],
            })
        else:
            prereq_details.append({"id": pid, "name": "Unknown", "credits": None})

    return {
        "course_id": course_id,
        "course_name": course["name"],
        "prerequisites": prereq_details,
    }


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
                "prerequisites": course["prerequisites"],
                "description": course["description"],
            })

    if not suggestions:
        return {"message": "No new courses available based on completed courses.", "suggestions": []}
    return {"suggestions": suggestions, "count": len(suggestions)}

#Server

app = Server("course-assistant")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_course",
            description="Search for courses by keyword. Matches against course ID, name, description, and topics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword, e.g. 'machine learning' or 'CS4680'",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_course_details",
            description="Get full details for a specific course by its course ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "string",
                        "description": "The course ID, e.g. 'CS4680'",
                    }
                },
                "required": ["course_id"],
            },
        ),
        Tool(
            name="list_courses_by_topic",
            description="Find all courses that cover a given topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to search for, e.g. 'recursion' or 'neural networks'",
                    }
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="check_prerequisites",
            description="Check what prerequisites are required before taking a course.",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "string",
                        "description": "The course ID to check prerequisites for, e.g. 'CS3100'",
                    }
                },
                "required": ["course_id"],
            },
        ),
        Tool(
            name="suggest_next_courses",
            description="Given a list of completed course IDs, suggest which courses the student is now eligible to take.",
            inputSchema={
                "type": "object",
                "properties": {
                    "completed_courses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of completed course IDs, e.g. ['CS1010', 'CS2050']",
                    }
                },
                "required": ["completed_courses"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "search_course":
        query = arguments.get("query", "")
        result = search_course(query)

    elif name == "get_course_details":
        course_id = arguments.get("course_id", "")
        result = get_course_details(course_id)

    elif name == "list_courses_by_topic":
        topic = arguments.get("topic", "")
        result = list_courses_by_topic(topic)

    elif name == "check_prerequisites":
        course_id = arguments.get("course_id", "")
        result = check_prerequisites(course_id)

    elif name == "suggest_next_courses":
        completed = arguments.get("completed_courses", [])
        result = suggest_next_courses(completed)

    else:
        result = {"error": f"Unknown tool '{name}'."}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


#Entry Point
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
