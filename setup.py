from setuptools import setup, find_packages

setup(
    name="remote-pydantic-settings",
    version="0.2.1",
    description="Pydantic Settings with remote sources (Redis, HTTP/HTTPS) via .env URLs with JSON extraction",
    author="anixvoid",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pydantic-settings>=2.0",
    ],
    extras_require={
        "redis": ["redis>=4.0"],
        "http": ["requests>=2.0"],
        "all": ["redis>=4.0", "requests>=2.0"],
    },
)