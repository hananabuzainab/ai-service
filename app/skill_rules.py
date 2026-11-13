
import re
import math


ALIASES = {
    # Programming languages
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",

    # Databases
    "postgres": "postgresql",
    "postgre sql": "postgresql",
    "ms sql": "sql server",
    "mssql": "sql server",
    "mongo": "mongodb",

    # JavaScript ecosystem
    "node": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "expressjs": "express",
    "express.js": "express",
    "nextjs": "next.js",

    # Cloud
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "amazon web services": "aws",
    "amazon ec2": "ec2",
    "amazon s3": "s3",
    "aws lambda": "lambda",
    "microsoft azure": "azure",

    # Machine Learning
    "ml": "machine learning",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "tf": "tensorflow",
    "opencv-python": "opencv",

    # APIs
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "restful": "rest api",

    # DevOps
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "travis ci": "travisci",
    "gitlab ci/cd": "gitlab ci",
    "github action": "github actions",

    # Security
    "json web token": "jwt",
    "json web tokens": "jwt",

    # CSS ecosystem
    "tailwind": "tailwind css",
}


NO_SPLIT = {
    "ci/cd",
    "tcp/ip",
}


# Strong relationships only.
# Weak relationships are intentionally excluded from automatic skill addition.
IMPLIES = {
    # Databases -> SQL
    "postgresql": ["sql"],
    "mysql": ["sql"],
    "sqlite": ["sql"],
    "mariadb": ["sql"],
    "sql server": ["sql"],

    # Python ecosystem
    "flask": ["python"],
    "django": ["python"],
    "fastapi": ["python"],
    "pandas": ["python"],
    "numpy": ["python"],
    "matplotlib": ["python"],
    "scikit-learn": ["python"],
    "pytest": ["python"],
    "celery": ["python"],

    # Other frameworks
    "laravel": ["php"],
    "symfony": ["php"],
    "spring boot": ["java"],
    "junit": ["java"],
    "rails": ["ruby"],

    # JavaScript ecosystem
    "node.js": ["javascript"],
    "express": ["node.js"],

    # CSS ecosystem
    "tailwind css": ["css"],
    "sass": ["css"],
    "bootstrap": ["css"],

    # Cloud and DevOps
    "docker compose": ["docker"],
    "helm": ["kubernetes"],
    "travisci": ["ci/cd"],
    "gitlab ci": ["ci/cd"],
    "circleci": ["ci/cd"],

    # AWS services
    "ec2": ["aws"],
    "s3": ["aws"],
    "lambda": ["aws"],
    "dynamodb": ["aws"],
    "rds": ["aws"],
    "eks": ["aws", "kubernetes"],

    # Google Cloud
    "bigquery": ["google cloud platform"],
}


CATEGORY = {
    # Programming languages
    "sql": "languages",
    "python": "languages",
    "php": "languages",
    "java": "languages",
    "javascript": "languages",
    "typescript": "languages",
    "ruby": "languages",
    "go": "languages",
    "css": "languages",
    "html": "languages",
    "c": "languages",
    "c++": "languages",

    # Databases
    "postgresql": "databases",
    "mysql": "databases",
    "sqlite": "databases",
    "mariadb": "databases",
    "sql server": "databases",
    "mongodb": "databases",

    # Frameworks and libraries
    "flask": "frameworks",
    "django": "frameworks",
    "fastapi": "frameworks",
    "laravel": "frameworks",
    "symfony": "frameworks",
    "spring boot": "frameworks",
    "react": "frameworks",
    "vue": "frameworks",
    "next.js": "frameworks",
    "express": "frameworks",
    "node.js": "frameworks",
    "rails": "frameworks",
    "tailwind css": "frameworks",
    "sass": "frameworks",
    "bootstrap": "frameworks",
    "celery": "frameworks",
    "pytest": "frameworks",
    "junit": "frameworks",

    # Machine Learning and Data
    "pandas": "ml_data",
    "numpy": "ml_data",
    "matplotlib": "ml_data",
    "scikit-learn": "ml_data",
    "machine learning": "ml_data",
    "tensorflow": "ml_data",
    "pytorch": "ml_data",
    "opencv": "ml_data",
    "yolo": "ml_data",
    "keras": "ml_data",
    "scipy": "ml_data",

    # Cloud and DevOps
    "docker": "cloud_devops",
    "docker compose": "cloud_devops",
    "kubernetes": "cloud_devops",
    "helm": "cloud_devops",
    "ci/cd": "cloud_devops",
    "github actions": "cloud_devops",
    "jenkins": "cloud_devops",
    "travisci": "cloud_devops",
    "gitlab ci": "cloud_devops",
    "circleci": "cloud_devops",
    "aws": "cloud_devops",
    "ec2": "cloud_devops",
    "s3": "cloud_devops",
    "lambda": "cloud_devops",
    "dynamodb": "cloud_devops",
    "rds": "cloud_devops",
    "eks": "cloud_devops",
    "google cloud platform": "cloud_devops",
    "bigquery": "cloud_devops",
    "azure": "cloud_devops",
    "linux": "cloud_devops",

    # Tools
    "git": "tools",
    "github": "tools",
    "gitlab": "tools",
    "bitbucket": "tools",
    "maven": "tools",
    "jupyter": "tools",
    "postman": "tools",
    "power bi": "tools",
    "vscode": "tools",

    # Other technical concepts
    "rest api": "other",
    "jwt": "other",
}


IMPLIED_CONFIDENCE_CAP = 0.70


def _score(item, key):
    value = item.get(key)

    if isinstance(value, bool):
        return None

    if isinstance(value, str):
        try:
            value = float(value.strip())
        except ValueError:
            return None

    if not isinstance(value, (int, float)):
        return None

    value = float(value)

    if not math.isfinite(value):
        return None

    return min(max(value, 0.0), 1.0)


def _best(a, b):
    if a is None:
        return b

    if b is None:
        return a

    return max(a, b)


def _known_names():
    names = set(ALIASES)
    names.update(ALIASES.values())
    names.update(IMPLIES)
    names.update(CATEGORY)

    for parents in IMPLIES.values():
        names.update(parents)

    return names


def _canonical_parts(raw_name):
    if not isinstance(raw_name, str):
        return []

    name = re.sub(
        r"\s+",
        " ",
        raw_name.strip().lower()
    )

    if not name:
        return []

    pieces = [name]

    # Extract skills inside parentheses.
    # Example: SQL (Postgres) -> SQL + Postgres
    match = re.match(
        r"^(.+?)\s+\(([^()]+)\)\s*$",
        name
    )

    if match and match.group(1):
        base = match.group(1).strip()
        inner = match.group(2).strip()

        pieces = [base]

        inner = ALIASES.get(inner, inner)

        if inner in _known_names():
            pieces.append(inner)

    parts = []

    for piece in pieces:

        # Apply aliases before splitting.
        # This prevents "gitlab ci/cd" from becoming
        # "gitlab ci" + "cd".
        piece = ALIASES.get(piece, piece)

        if piece in NO_SPLIT:
            parts.append(piece)
        else:
            parts.extend(
                part.strip()
                for part in piece.split("/")
                if part.strip()
            )

    return [
        ALIASES.get(part, part)
        for part in parts
    ]


def refine_skills(skills, score_key, cap_implied=None):
    merged = {}

    def put(name, category, score):
        if name in merged:
            merged[name]["score"] = _best(
                merged[name]["score"],
                score
            )
        else:
            merged[name] = {
                "category": category,
                "score": score
            }

    # First, normalize and merge explicitly extracted skills.
    for item in skills or []:
        if not isinstance(item, dict):
            continue

        score = _score(item, score_key)

        for name in _canonical_parts(item.get("name", "")):
            category = (
                CATEGORY.get(name)
                or str(item.get("category", "other")).strip().lower()
            )

            put(name, category, score)

    # Keep track of skills explicitly extracted by the LLM.
    explicit_names = set(merged)

    # Add strongly implied skills without overwriting
    # explicitly extracted skills or their scores.
    for name, info in list(merged.items()):
        for parent in IMPLIES.get(name, []):

            if parent in explicit_names:
                continue

            score = info["score"]

            if cap_implied is not None and score is not None:
                score = min(score, cap_implied)

            put(
                parent,
                CATEGORY.get(parent, "other"),
                score
            )

    result = []

    for name, info in merged.items():
        score = info["score"]

        result.append({
            "name": name,
            "category": info["category"],
            score_key: (
                None
                if score is None
                else round(min(max(score, 0.0), 1.0), 2)
            )
        })

    return result


def refine_resume_skills(skills):
    return refine_skills(
        skills,
        "confidence_score",
        cap_implied=IMPLIED_CONFIDENCE_CAP
    )


def refine_job_skills(skills):
    return refine_skills(
        skills,
        "importance"
    )
