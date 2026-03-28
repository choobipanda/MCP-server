import pytest
from unittest.mock import patch

from mcp_server import (
    search_course,
    get_course_details,
    list_courses_by_topic,
    check_prerequisites,
    suggest_next_courses,
)

#my courses

SAMPLE_COURSES = [
    {
        "id": "STA2260",
        "name": "Probability and Statistics for Computer Scientists and Engineers",
        "credits": 3,
        "instructor": "Prof. Jay Windley",
        "email": "jcwindley@cpp.edu",
        "schedule": "Tue/Thu 5:30PM-6:45PM",
        "room": "9-277",
        "topics": ["descriptive statistics", "probability", "hypothesis testing", "regression", "ANOVA"],
        "prerequisites": ["MAT1150 or MAT1310 with C or better"],
        "description": "Calculus-based introductory statistics covering probability, distributions, and inference.",
    },
    {
        "id": "CS2250",
        "name": "Introduction to Web Science and Technology",
        "credits": 3,
        "instructor": "Dr. J (Dr. Johannsen)",
        "email": "dljohannsen@cpp.edu",
        "schedule": "In-person (see Canvas)",
        "room": "See Canvas",
        "topics": ["HTML markup", "CSS stylesheets", "JavaScript", "client-side scripting", "server-side scripting", "web security"],
        "prerequisites": ["CS1400 or CS1260 or CS1280 with C or better"],
        "description": "Covers fundamentals of the web including HTML, CSS, JavaScript, and web app development.",
    },
    {
        "id": "CS4680",
        "name": "Prompt Engineering",
        "credits": 3,
        "instructor": "Prof. Abdelfattah Amamra",
        "email": "aamamra@cpp.edu",
        "schedule": "Tue 1:00PM-2:15PM in-person, Thu online asynchronous",
        "room": "8-348",
        "topics": ["LLM training", "prompt engineering", "prompt patterns", "RAG", "agents", "MCP", "transformers"],
        "prerequisites": ["CS2400 or equivalent, Python or Java proficiency"],
        "description": "Covers LLM training, prompt engineering patterns, RAG, agents, and MCP.",
    },
    {
        "id": "CS3010",
        "name": "Numerical Methods",
        "credits": 3,
        "instructor": "Lecturer Edwin Rodriguez",
        "email": "earodriguez@cpp.edu",
        "schedule": "Mon/Wed/Fri 11:00AM-11:50AM",
        "room": "Building 8, Room 302",
        "topics": ["error analysis", "root finding", "interpolation", "numerical integration", "linear equations"],
        "prerequisites": ["Calculus", "Linear Algebra", "Programming proficiency"],
        "description": "Introduction to numerical methods and their implementation as computer programs.",
    },
    {
        "id": "CS4080",
        "name": "Programming Languages",
        "credits": 3,
        "instructor": "Lecturer Edwin Rodriguez",
        "email": "earodriguez@cpp.edu",
        "schedule": "Mon/Wed/Fri 9:00AM-9:50AM",
        "room": "8-345",
        "topics": ["syntax and semantics", "binding and scoping", "data types", "control flow", "programming paradigms", "runtime processing"],
        "prerequisites": ["Upper division CS standing"],
        "description": "Design and implementation of programming languages covering syntax, semantics, types, and paradigms.",
    },
]


@pytest.fixture(autouse=True)
def mock_courses():
    with patch("mcp_server.load_courses", return_value=SAMPLE_COURSES):
        yield

#search_course

class TestSearchCourse:
    def test_match_by_course_id(self):
        result = search_course("CS4680")
        assert result["count"] == 1
        assert result["results"][0]["id"] == "CS4680"

    def test_match_by_name(self):
        result = search_course("web science")
        assert result["count"] == 1
        assert result["results"][0]["id"] == "CS2250"

    def test_match_by_topic(self):
        result = search_course("RAG")
        assert result["count"] == 1
        assert result["results"][0]["id"] == "CS4680"

    def test_match_by_description(self):
        result = search_course("numerical methods")
        assert result["count"] == 1
        assert result["results"][0]["id"] == "CS3010"

    def test_no_match_returns_empty(self):
        result = search_course("quantum computing")
        assert result["results"] == []
        assert "No courses found" in result["message"]

    def test_empty_query_returns_error(self):
        result = search_course("")
        assert "error" in result

    def test_case_insensitive(self):
        result = search_course("PROMPT ENGINEERING")
        assert result["count"] >= 1

#get_course_details

class TestGetCourseDetails:
    def test_valid_course_id(self):
        result = get_course_details("CS4680")
        assert result["id"] == "CS4680"
        assert result["name"] == "Prompt Engineering"
        assert "topics" in result
        assert "prerequisites" in result

    def test_case_insensitive_id(self):
        result = get_course_details("cs4680")
        assert result["id"] == "CS4680"

    def test_sta_course(self):
        result = get_course_details("STA2260")
        assert result["id"] == "STA2260"
        assert "Windley" in result["instructor"]

    def test_invalid_course_id_returns_error(self):
        result = get_course_details("CS9999")
        assert "error" in result

    def test_empty_id_returns_error(self):
        result = get_course_details("")
        assert "error" in result

#list_courses_by_topic

class TestListCoursesByTopic:
    def test_known_topic(self):
        result = list_courses_by_topic("regression")
        assert result["count"] == 1
        assert result["results"][0]["id"] == "STA2260"

    def test_topic_shared_by_multiple_courses(self):
        result = list_courses_by_topic("scripting")
        ids = [r["id"] for r in result["results"]]
        assert "CS2250" in ids

    def test_unknown_topic_returns_empty(self):
        result = list_courses_by_topic("blockchain")
        assert result["results"] == []
        assert "No courses" in result["message"]

    def test_empty_topic_returns_error(self):
        result = list_courses_by_topic("")
        assert "error" in result

    def test_case_insensitive(self):
        result = list_courses_by_topic("MCP")
        assert result["count"] == 1
        assert result["results"][0]["id"] == "CS4680"

#check_prerequisites

class TestCheckPrerequisites:
    def test_course_with_prereqs(self):
        result = check_prerequisites("CS4680")
        assert "prerequisites" in result
        assert len(result["prerequisites"]) > 0

    def test_returns_course_name(self):
        result = check_prerequisites("CS3010")
        assert result["course_name"] == "Numerical Methods"

    def test_invalid_course_returns_error(self):
        result = check_prerequisites("CS9999")
        assert "error" in result

    def test_empty_id_returns_error(self):
        result = check_prerequisites("")
        assert "error" in result

    def test_case_insensitive(self):
        result = check_prerequisites("cs4680")
        assert result["course_id"] == "CS4680"

#suggest_next_courses

class TestSuggestNextCourses:
    def test_no_completed_courses_returns_error(self):
        result = suggest_next_courses([])
        assert "error" in result

    def test_does_not_suggest_already_completed(self):
        all_ids = [c["id"] for c in SAMPLE_COURSES]
        result = suggest_next_courses(all_ids)
        completed_set = set(all_ids)
        for s in result.get("suggestions", []):
            assert s["id"] not in completed_set

    def test_returns_suggestions_key(self):
        result = suggest_next_courses(["CS4680"])
        assert "suggestions" in result

    def test_case_insensitive_ids(self):
        result1 = suggest_next_courses(["CS4680"])
        result2 = suggest_next_courses(["cs4680"])
        assert result1["suggestions"] == result2["suggestions"]

    def test_no_suggestions_when_all_completed(self):
        all_ids = [c["id"] for c in SAMPLE_COURSES]
        result = suggest_next_courses(all_ids)
        assert result["suggestions"] == []
