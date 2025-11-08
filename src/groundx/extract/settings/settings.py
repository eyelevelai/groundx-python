import json, typing, os

from pydantic import BaseModel


AWS_REGION: str = "AWS_REGION"
AWS_DEFAULT_REGION: str = "AWS_DEFAULT_REGION"


GX_AGENT_KEY: str = "GROUNDX_AGENT_API_KEY"
CALLBACK_KEY: str = "GROUNDX_CALLBACK_API_KEY"
GCP_CREDENTIALS: str = "GCP_CREDENTIALS"
GX_API_KEY: str = "GROUNDX_API_KEY"
GX_KEY: str = "GROUNDX_ACCESS_KEY_ID"
GX_REGION: str = "GROUNDX_REGION"
GX_DEFAULT_REGION: str = "GROUNDX_DEFAULT_REGION"
GX_SECRET: str = "GROUNDX_SECRET_ACCESS_KEY"
GX_TOKEN: str = "GROUNDX_SESSION_TOKEN"
VALID_KEYS: str = "GROUNDX_VALID_API_KEYS"
GX_ADMIN_API_KEY: str = "GROUNDX_ADMIN_API_KEY"
GX_ADMIN_USERNAME: str = "GROUNDX_ADMIN_USERNAME"


class AgentSettings(BaseModel):
    api_base: typing.Optional[str] = None
    api_key: typing.Optional[str] = None
    imports: typing.List[str] = [
        "csv",
        "glob",
        "io",
        "json",
        "markdown",
        "numpy",
        "os",
        "pandas",
        "posixpath",
        "open",
        "builtins.open",
        "utils.safe_open",
        "pydantic",
        "typing",
    ]
    max_steps: int = 7
    model_id: str = "gpt-5-mini"

    def get_api_key(self) -> str:
        if self.api_key:
            return self.api_key

        key = os.environ.get(GX_AGENT_KEY)
        if key:
            return key

        raise Exception(f"you must set a valid agent api_key")


class ContainerSettings(BaseModel):
    broker: str
    broker_type: str = "redis"
    cache_dir: str = "./cache"
    cache_to: int = 300
    google_sheets_drive_id: typing.Optional[str] = None
    google_sheets_template_id: typing.Optional[str] = None
    log_level: str = "info"
    metrics_broker: typing.Optional[str] = None
    refresh_to: int = 60
    service: str
    task_to: int = 600
    upload: "ContainerUploadSettings"
    workers: int

    callback_api_key: typing.Optional[str] = None
    valid_api_keys: typing.Optional[typing.List[str]] = None

    def get_callback_api_key(self) -> str:
        if self.callback_api_key:
            return self.callback_api_key

        key = os.environ.get(CALLBACK_KEY)
        if key:
            return key

        key = os.environ.get(GX_ADMIN_USERNAME)
        if key:
            return key

        key = os.environ.get(GX_ADMIN_API_KEY)
        if key:
            return key

        key = os.environ.get(GX_API_KEY)
        if key:
            return key

        raise Exception(f"you must set a callback_api_key")

    def get_valid_api_keys(self) -> typing.List[str]:
        keys: typing.List[str] = []

        if self.valid_api_keys:
            keys = self.valid_api_keys

        env_keys: typing.Optional[str] = os.environ.get(VALID_KEYS)
        if env_keys:
            try:
                data: typing.List[str] = json.loads(env_keys)
                keys.extend(data)
            except Exception as e:
                raise Exception(f"you must set an array of valid_api_keys: {e}")

        key = os.environ.get(CALLBACK_KEY)
        if key:
            keys.append(key)

        key = os.environ.get(GX_ADMIN_API_KEY)
        if key:
            keys.append(key)

        key = os.environ.get(GX_ADMIN_USERNAME)
        if key:
            keys.append(key)

        key = os.environ.get(GX_API_KEY)
        if key:
            keys.append(key)

        if len(keys) < 1:
            raise Exception(f"you must set an array of valid_api_keys")

        return keys

    def loglevel(self) -> str:
        return self.log_level.upper()

    def status_broker(self) -> str:
        if self.metrics_broker:
            return self.metrics_broker

        return self.broker


class ContainerUploadSettings(BaseModel):
    base_domain: str
    base_path: str = "layout/processed/"
    bucket: str
    ssl: bool = False
    type: str
    url: str

    key: typing.Optional[str] = None
    region: typing.Optional[str] = None
    secret: typing.Optional[str] = None
    token: typing.Optional[str] = None

    def get_key(self) -> typing.Optional[str]:
        if self.key:
            return self.key

        return os.environ.get(GX_KEY)

    def get_region(self) -> typing.Optional[str]:
        if self.region:
            return self.region

        key = os.environ.get(GX_REGION)
        if key:
            return key

        key = os.environ.get(AWS_REGION)
        if key:
            return key

        key = os.environ.get(GX_DEFAULT_REGION)
        if key:
            return key

        return os.environ.get(AWS_DEFAULT_REGION)

    def get_secret(self) -> typing.Optional[str]:
        if self.secret:
            return self.secret

        return os.environ.get(GX_SECRET)

    def get_token(self) -> typing.Optional[str]:
        if self.token:
            return self.token

        return os.environ.get(GX_TOKEN)


class GroundXSettings(BaseModel):
    api_key: typing.Optional[str] = None
    base_url: typing.Optional[str] = None
    upload_url: str = "https://upload.eyelevel.ai"

    def get_api_key(self) -> str:
        if self.api_key:
            return self.api_key

        key = os.environ.get(GX_ADMIN_USERNAME)
        if key:
            return key

        key = os.environ.get(GX_API_KEY)
        if key:
            return key

        key = os.environ.get(GX_ADMIN_API_KEY)
        if key:
            return key

        raise Exception(f"you must set a valid GroundX api_key")
