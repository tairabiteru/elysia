import dataclasses
import hikari
import pathlib
import toml
import typing as t
import zoneinfo

from .log_base import get_base_logger


logger = get_base_logger()

__VERSION__ : str = "0.1.0"
__TAG__: str = "Hopeful Humanitarian"

DEFAULTS = {
    'name': 'Elysia',
    'timezone': 'UTC',
    'root': '/path/to/elysia/root',
    'temp': '/dev/shm/elysia',
    'logs': '/path/to/elysia/root/logs',
    'owner_id': 123456789012345678,
    'token': 'discord_api_token',
    'fqdn': 'example.com',
    'logging': {
        'format': '[%(levelletter)s][%(asctime)s][%(name)s] %(message)s',
        'date_format': '%x %X',
        'levels': {
            'hikari': 'WARNING',
            'lightbulb': 'WARNING',
            'uvicorn': 'WARNING',
            'bot': 'INFO'
        },
    },
    'mvc': {
        'enable_http': True,
        'fernet_key': 'some_fernet_key',
        'client_secret': 'discord_oauth_client_secret',
        'secret_key': 'django_secret_key',
        'host': 'localhost',
        'port': 8080,
        'allowed_hosts': ["example.com", "localhost"],
        'static_root': '/path/to/elysia/root/static/',
        'upload_root': '/path/to/elysia/root/uploads/',
        'debug_mode': False,
        'database': {
            'backup_dir': '/path/to/elysia/root/db_backups/',
            'path': '/path/to/db'
        }
    }
}


class BaseConfig:
    _sub_fields: t.Tuple[str, ...]
    __dataclass_fields__: t.Dict

    @classmethod
    def _dict_load(cls, d: dict):
        args = []
        for name, field in cls.__dataclass_fields__.items():
            if name == "_sub_fields":
                continue
            try:
                value = d.pop(name)
                
                try:
                    sub_fields = getattr(cls, "_sub_fields")
                except AttributeError:
                    sub_fields = []
                
                if name in sub_fields:
                
                    args.append(field.type._dict_load(value))
                else:
                    try:
                        args.append(field.type(value))
                    except TypeError:
                        args.append(value)
            except KeyError:
                raise RuntimeError(f"Field '{name}' missing from config for {cls.__name__}.")

        if d:
            fields = ", ".join(d.keys())
            raise RuntimeError(f"Unknown fields {fields} detected in config for {cls.__name__}.")
        
        return cls(*args)


@dataclasses.dataclass
class LogConfig(BaseConfig):
    format: str
    date_format: str
    levels: t.Dict[str, str]


@dataclasses.dataclass
class DatabaseConfig(BaseConfig):
    backup_dir: pathlib.Path
    path: pathlib.Path


@dataclasses.dataclass
class MVCConfig(BaseConfig):
    enable_http: bool
    fernet_key: str
    client_secret: str
    secret_key: str
    host: str
    port: int
    allowed_hosts: t.List[str]
    static_root: pathlib.Path
    upload_root: pathlib.Path
    debug_mode: bool
    database: DatabaseConfig

    _sub_fields: t.Tuple[str] = ("database", )


@dataclasses.dataclass
class GeneralConfig(BaseConfig):
    name: str
    timezone: zoneinfo.ZoneInfo
    root: pathlib.Path
    temp: pathlib.Path
    logs: pathlib.Path
    owner_id: hikari.Snowflake
    token: str
    fqdn: str

    logging: LogConfig
    mvc: MVCConfig

    _sub_fields: t.Tuple[str, ...] = ("logging", "mvc", "voice", )
    
    @property
    def version(self) -> str:
        return __VERSION__
    
    @property
    def version_tag(self) -> str:
        return __TAG__
    
    @property
    def root_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parent.parent.parent
    
    @property
    def log_dir(self) -> pathlib.Path:
        return self.logs
    
    @property
    def asset_dir(self) -> pathlib.Path:
        return self.root_dir / "assets/"
    
    @property
    def bin_dir(self) -> pathlib.Path:
        return self.root_dir / "bin/"
    
    @property
    def outfacing_url(self) -> str:
        return self.mvc.allowed_hosts[0]

    @classmethod
    def load(cls):
        try:
            with open("conf.toml", "r") as conf_file:
                config_dict = toml.load(conf_file)
            return cls._dict_load(config_dict)
        except FileNotFoundError:
            with open("conf.toml", "w") as config_file:
                toml.dump(DEFAULTS, config_file)

            logger.critical("No configuration file found.")
            logger.critical("A default file will be created, but it must be configured before a successful boot.")
            raise RuntimeError("Invalid config.")

Config = GeneralConfig