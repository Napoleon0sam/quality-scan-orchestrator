import json
import os
import subprocess

api_token = os.environ.get("API_TOKEN", "")

def parse_value(value: str):
    return json.loads(value)

def run_echo(value: str):
    return subprocess.run(["echo", value], check=True)

def divide(value: int):
    try:
        return 10 / value
    except ZeroDivisionError:
        return None

def short_function():
    return 1
