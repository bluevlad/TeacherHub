"""
TeacherHub AI Crawler Setup
"""
from setuptools import setup, find_packages

setup(
    name="teacherhub-crawler",
    version="2.0.0",
    description="TeacherHub AI Crawler - 강사 평판 분석 시스템",
    author="bluevlad",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "playwright>=1.40.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "apscheduler>=3.10.0",
        "flask>=3.0.0",
        "textblob>=0.17.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "teacherhub=src.cli:main",
        ],
    },
)
