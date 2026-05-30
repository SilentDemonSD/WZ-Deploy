from sys import exit
from importlib import import_module
from logging import (
    FileHandler,
    StreamHandler,
    INFO,
    basicConfig,
    error as log_error,
    info as log_info,
    getLogger,
    ERROR,
)
from os import path, remove, environ
import asyncio
from pymongo.asynchronous import AsyncMongoClient
from pymongo.server_api import ServerApi
from subprocess import run as srun, call as scall

getLogger("pymongo").setLevel(ERROR)

var_list = ['BOT_TOKEN', 'TELEGRAM_API', 'TELEGRAM_HASH', 'OWNER_ID', 'DATABASE_URL', 'BASE_URL', 'UPSTREAM_REPO', 'UPSTREAM_BRANCH']

basicConfig(
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%d-%b-%y %I:%M:%S %p",
    handlers=[FileHandler("log.txt"), StreamHandler()],
    level=INFO,
)
try:
    settings = import_module("config")
    config_file = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in vars(settings).items()
        if not key.startswith("__")
    }
except ModuleNotFoundError:
    log_info("Config.py file is not Added! Checking ENVs..")
    config_file = {}

env_updates = {key: value.strip() if isinstance(value, str) else value for key, value in environ.items() if key in var_list}
if env_updates:
    log_info("Config data is updated with ENVs!")
    config_file.update(env_updates)

BOT_TOKEN = config_file.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    log_error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

BOT_ID = BOT_TOKEN.split(":", 1)[0]

async def fetch_config_from_db():
    """Fetch configuration from MongoDB asynchronously."""
    database_url = config_file.get("DATABASE_URL", "").strip()
    if not database_url:
        return
    
    try:
        async with AsyncMongoClient(database_url, server_api=ServerApi("1")) as conn:
            db = conn.wzmlx
            old_config = await db.settings.deployConfig.find_one({"_id": BOT_ID}, {"_id": 0})
            config_dict = await db.settings.config.find_one({"_id": BOT_ID})
            if (
                old_config is not None and old_config == config_file or old_config is None
            ) and config_dict is not None:
                config_file["UPSTREAM_REPO"] = config_dict["UPSTREAM_REPO"]
                config_file["UPSTREAM_BRANCH"] = config_dict.get("UPSTREAM_BRANCH", "wzv3")
                config_file["UPDATE_PKGS"] = config_dict.get("UPDATE_PKGS", "True")
    except Exception as e:
        log_error(f"Database ERROR: {e}")

if DATABASE_URL := config_file.get("DATABASE_URL", "").strip():
    asyncio.run(fetch_config_from_db())

UPSTREAM_REPO = config_file.get("UPSTREAM_REPO", "").strip()
UPSTREAM_BRANCH = config_file.get("UPSTREAM_BRANCH", "").strip() or "wzv3"

if UPSTREAM_REPO:
    if path.exists(".git"):
        srun(["rm", "-rf", ".git"])

    update = srun(
        [
            f"git init -q \
                     && git config --global user.email 105407900+SilentDemonSD@users.noreply.github.com \
                     && git config --global user.name SilentDemonSD \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"
        ],
        shell=True,
    )

    repo = UPSTREAM_REPO.split("/")
    UPSTREAM_REPO = f"https://github.com/{repo[-2]}/{repo[-1]}"
    if update.returncode == 0:
        log_info("Successfully updated with Latest Updates !")
    else:
        log_error("Something went Wrong ! Recheck your details or Ask Support !")
    log_info(f"UPSTREAM_REPO: {UPSTREAM_REPO} | UPSTREAM_BRANCH: {UPSTREAM_BRANCH}")


UPDATE_PKGS = config_file.get("UPDATE_PKGS", "True")
if (isinstance(UPDATE_PKGS, str) and UPDATE_PKGS.lower() == "true") or UPDATE_PKGS:
    scall("uv pip install -U -r requirements.txt", shell=True)
    log_info("Successfully Updated all the Packages !")
