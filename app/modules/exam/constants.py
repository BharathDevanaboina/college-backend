"""The TS ICET-style pattern every question set must follow."""

SLOTS = (1, 2, 3)

SECTION_TITLES = {
    "A": "Analytical Ability",
    "B": "Mathematical Ability",
    "C": "Communication Ability",
}

# An upload is rejected if these counts are not met.
REQUIRED_SECTION_COUNTS = {"A": 75, "B": 75, "C": 50}
TOTAL_QUESTIONS = sum(REQUIRED_SECTION_COUNTS.values())  # 200

# Checked as warnings only.
EXPECTED_SUBSECTION_COUNTS = {
    "A": {"Data Sufficiency": 20, "Problem Solving": 55},
    "B": {
        "Arithmetical Ability": 35,
        "Algebraical and Geometrical Ability": 30,
        "Statistical Ability": 10,
    },
    "C": {
        "Vocabulary": 15,
        "Business and Computer Terminology": 10,
        "Functional Grammar": 15,
        "Reading Comprehension": 10,
    },
}

OPTION_LABELS = ("A", "B", "C", "D")
MAX_ROWS = 1000
MAX_TEXT_LENGTH = 5000
MAX_OPTION_LENGTH = 1000
