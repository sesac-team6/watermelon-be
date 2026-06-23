from setuptools import find_packages, setup


setup(
    name="watermelon-backend",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "fastapi>=0.115.0",
        "pydantic-settings>=2.4.0",
        "psycopg[binary]>=3.2.0",
        "sqlalchemy>=2.0.0",
        "uvicorn[standard]>=0.30.0",
    ],
    extras_require={
        "dev": [
            "httpx>=0.27.0",
            "pytest>=8.0.0",
            "ruff>=0.6.0",
        ],
    },
    python_requires=">=3.9",
)
