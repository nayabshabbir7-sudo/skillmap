"""Static learning content: practical tasks and interview questions."""

ACTION_PLANS = {
    "Data Analyst Intern": [
        {
            "title": "SQL Practice",
            "task": "Write SQL queries to filter, sort, and group sample data.",
            "outcome": "Save at least 5 practice queries.",
        },
        {
            "title": "Excel Data Cleaning",
            "task": "Clean a sample spreadsheet by handling duplicates and missing values.",
            "outcome": "Create a cleaned spreadsheet.",
        },
        {
            "title": "Pandas Analysis",
            "task": "Load a CSV file with Pandas and calculate useful summary statistics.",
            "outcome": "Write a Python script that analyzes the dataset.",
        },
        {
            "title": "Data Visualization",
            "task": "Create at least 2 charts from a dataset and explain what they show.",
            "outcome": "Save the charts and a short explanation.",
        },
        {
            "title": "Portfolio Project",
            "task": "Combine data cleaning, analysis, and visualization in one project.",
            "outcome": "Prepare a README and upload your project to GitHub.",
        },
    ],
    "Python Intern": [
        {
            "title": "Python Problem Solving",
            "task": "Solve 5 beginner problems using variables, conditions, and loops.",
            "outcome": "Save your solutions in Python files.",
        },
        {
            "title": "Functions Practice",
            "task": "Write reusable functions with parameters and return values.",
            "outcome": "Create a small collection of tested functions.",
        },
        {
            "title": "Working with Data",
            "task": "Build a program that processes a list or dictionary of records.",
            "outcome": "Print a useful summary of the data.",
        },
        {
            "title": "GitHub Practice",
            "task": "Create a repository and upload your Python practice project.",
            "outcome": "Add a README explaining how to run it.",
        },
        {
            "title": "Portfolio Project",
            "task": "Build a small command-line application using your Python skills.",
            "outcome": "Upload the code and documentation to GitHub.",
        },
    ],
    "Web Developer Intern": [
        {
            "title": "HTML Page",
            "task": "Create a webpage with headings, paragraphs, links, and images.",
            "outcome": "Save a working HTML page.",
        },
        {
            "title": "CSS Styling",
            "task": "Style your webpage with colors, spacing, and a responsive layout.",
            "outcome": "Create a consistent page design.",
        },
        {
            "title": "JavaScript Interaction",
            "task": "Add a button that changes page content when clicked.",
            "outcome": "Test the interaction in your browser.",
        },
        {
            "title": "Version Control",
            "task": "Upload your webpage project to GitHub.",
            "outcome": "Add a README with setup instructions.",
        },
        {
            "title": "Portfolio Project",
            "task": "Build a small multi-section personal portfolio website.",
            "outcome": "Document the project and prepare it for demonstration.",
        },
    ],
}


# Each question has a stable id (used to save progress), the question and a
# short hint describing what a good answer covers.
INTERVIEW_QUESTIONS = {
    "Python Intern": [
        {
            "id": "py-1",
            "question": "What is the difference between a list and a tuple?",
            "hint": "Lists are mutable and tuples are immutable. Tuples can be used as dictionary keys "
                    "(if their items are hashable) and suit fixed collections of values.",
        },
        {
            "id": "py-2",
            "question": "What are *args and **kwargs?",
            "hint": "*args collects extra positional arguments into a tuple, **kwargs collects extra "
                    "keyword arguments into a dictionary. They let a function accept a flexible number of arguments.",
        },
        {
            "id": "py-3",
            "question": "What is the difference between 'is' and '=='?",
            "hint": "'==' compares values for equality, 'is' checks whether two names point to the exact same object.",
        },
        {
            "id": "py-4",
            "question": "What is a decorator?",
            "hint": "A function that takes another function and returns a new one that adds behaviour "
                    "(logging, timing, access checks) without changing the original code. Applied with @.",
        },
        {
            "id": "py-5",
            "question": "Why do we use virtual environments?",
            "hint": "They isolate project dependencies so different projects can use different package versions, "
                    "and a requirements file makes the setup reproducible.",
        },
        {
            "id": "py-6",
            "question": "Explain the four pillars of object-oriented programming.",
            "hint": "Encapsulation (bundle data and methods), abstraction (hide complexity), inheritance "
                    "(reuse behaviour from a parent class) and polymorphism (same interface, different behaviour).",
        },
        {
            "id": "py-7",
            "question": "What is the difference between git commit, git push and git pull?",
            "hint": "Commit saves a snapshot locally, push uploads local commits to the remote repository, "
                    "pull downloads and merges changes from the remote.",
        },
    ],
    "Data Analyst Intern": [
        {
            "id": "da-1",
            "question": "What is the difference between INNER JOIN and LEFT JOIN?",
            "hint": "INNER JOIN returns only rows that match in both tables. LEFT JOIN returns all rows from the "
                    "left table and fills unmatched right-table columns with NULL.",
        },
        {
            "id": "da-2",
            "question": "What is the difference between WHERE and HAVING?",
            "hint": "WHERE filters individual rows before grouping, HAVING filters groups after aggregation.",
        },
        {
            "id": "da-3",
            "question": "How do you handle missing values in a dataset?",
            "hint": "First understand why they are missing. Then drop, fill (mean, median, mode, or a constant) "
                    "or flag them, depending on the amount of missing data and the business context.",
        },
        {
            "id": "da-4",
            "question": "When would you use the median instead of the mean?",
            "hint": "When the data is skewed or has outliers (for example salaries), because the median is not "
                    "pulled by extreme values.",
        },
        {
            "id": "da-5",
            "question": "How do you choose the right chart for your data?",
            "hint": "Comparison: bar chart. Trend over time: line chart. Relationship: scatter plot. "
                    "Distribution: histogram. Keep it simple and label axes clearly.",
        },
        {
            "id": "da-6",
            "question": "How would you check the quality of a new dataset?",
            "hint": "Check duplicates, data types, missing values, value ranges, outliers and consistency "
                    "between columns before starting any analysis.",
        },
        {
            "id": "da-7",
            "question": "Walk me through a data analysis project you have done.",
            "hint": "Use a clear flow: the question, the data source, cleaning steps, analysis, visualizations "
                    "and the final insight or recommendation.",
        },
    ],
    "Web Developer Intern": [
        {
            "id": "wd-1",
            "question": "What is the CSS box model?",
            "hint": "Every element is a box made of content, padding, border and margin, from the inside out.",
        },
        {
            "id": "wd-2",
            "question": "What is the difference between let, const and var in JavaScript?",
            "hint": "var is function-scoped and can be redeclared. let and const are block-scoped. "
                    "const cannot be reassigned (the contents of an object can still change).",
        },
        {
            "id": "wd-3",
            "question": "What is semantic HTML and why does it matter?",
            "hint": "Using elements like header, nav, main and article that describe meaning. It improves "
                    "accessibility, SEO and code readability.",
        },
        {
            "id": "wd-4",
            "question": "When would you use Flexbox and when CSS Grid?",
            "hint": "Flexbox lays out items in one dimension (a row or a column). Grid handles two dimensions "
                    "(rows and columns together).",
        },
        {
            "id": "wd-5",
            "question": "How do you make a website responsive?",
            "hint": "Mobile-first design, the viewport meta tag, flexible units (%, rem), flexible layouts "
                    "(Flexbox/Grid) and media queries.",
        },
        {
            "id": "wd-6",
            "question": "What happens when you type a URL into the browser?",
            "hint": "DNS lookup, connection to the server (TCP/TLS), HTTP request, server response, then the "
                    "browser parses HTML/CSS/JS and renders the page.",
        },
        {
            "id": "wd-7",
            "question": "What is the DOM?",
            "hint": "A tree representation of the page that JavaScript can read and change, for example to "
                    "update content or react to events.",
        },
    ],
}


HR_QUESTIONS = [
    {
        "id": "hr-1",
        "question": "Tell me about yourself.",
        "hint": "Keep it to about a minute: who you are, what you studied or built, and why this role.",
    },
    {
        "id": "hr-2",
        "question": "Why do you want this internship?",
        "hint": "Connect your skills and goals to what the company does. Mention one specific thing you like about it.",
    },
    {
        "id": "hr-3",
        "question": "Describe a project you are proud of.",
        "hint": "Explain the problem, what you built, the tools you used and what you learned or achieved.",
    },
    {
        "id": "hr-4",
        "question": "How do you learn a new technology quickly?",
        "hint": "Give a real example: official docs, a small practice project, then asking for feedback.",
    },
    {
        "id": "hr-5",
        "question": "Tell me about a time you faced a difficult problem.",
        "hint": "Use the STAR method: Situation, Task, Action, Result.",
    },
    {
        "id": "hr-6",
        "question": "Do you have any questions for us?",
        "hint": "Always ask one: about the team, the first-month goals or how interns are mentored.",
    },
]