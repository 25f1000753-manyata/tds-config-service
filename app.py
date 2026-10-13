

import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

ALLOWED_KEYS = set(DEFAULTS)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize(mapping, app_prefix_only=False):
    result = {}

    for key, value in mapping.items():
        if value is None:
            continue

        key = str(key).strip().lower()

        if app_prefix_only and not key.startswith("app_"):
            continue

        if key.startswith("app_"):
            key = key[4:]

        if key == "num_workers":
            key = "workers"

        if key in ALLOWED_KEYS:
            result[key] = value

    return result


def as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return as_bool(value)
    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # 1. Environment-specific YAML
    environment = os.environ.get("APP_ENV", "development")
    yaml_file = BASE_DIR / f"config.{environment}.yaml"

    if yaml_file.exists():
        with yaml_file.open(encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}

        if isinstance(yaml_config, dict):
            config.update(normalize(yaml_config))

    # 2. .env file
    env_file = dotenv_values(BASE_DIR / ".env")
    config.update(normalize(env_file))

    # 3. Operating-system environment variables
    config.update(normalize(os.environ, app_prefix_only=True))

    # 4. Query-string overrides, e.g. ?set=port=9000
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = key.strip().lower()

        if key.startswith("app_"):
            key = key[4:]

        if key == "num_workers":
            key = "workers"

        if key in ALLOWED_KEYS:
            config[key] = value

    result = {
        key: coerce(key, config[key])
        for key in DEFAULTS
    }

    # Never expose the actual API key
    result["api_key"] = "****"

    return result
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return as_bool(value)
    return str(value)


def normalize(mapping, strip_prefix=False):
    result = {}
    for key, value in mapping.items():
        if value is None:
            continue

        key = str(key).lower()
        if strip_prefix:
            if not key.startswith("app_"):
                continue
            key = key[4:]

        if key == "num_workers":
            key = "workers"

        result[key] = value

    return result


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # Environment-specific YAML layer
    environment = os.environ.get("APP_ENV", "development")
    yaml_file = BASE_DIR / f"config.{environment}.yaml"

    if yaml_file.exists():
        with yaml_file.open(encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}
        config.update(normalize(yaml_config))

    # .env layer
    env_file = dotenv_values(BASE_DIR / ".env")
    config.update(normalize(env_file))

    # OS-level environment variables take precedence over .env
    os_config = normalize(os.environ, strip_prefix=True)
    config.update(os_config)

    # CLI/query overrides have the highest precedence
    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip().lower()

        if key == "num_workers":
            key = "workers"

        config[key] = value

    # Coerce types and retain additional string-valued overrides
    result = {
        key: coerce(key, value)
        for key, value in config.items()
    }

    # Never reveal the real API key
    result["api_key"] = "****"

    return result
