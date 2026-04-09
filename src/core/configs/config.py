from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic_settings import (
	BaseSettings,
	EnvSettingsSource,
	JsonConfigSettingsSource,
	PydanticBaseSettingsSource,
	SettingsConfigDict,
	TomlConfigSettingsSource,
)

from src.core.configs.app import App, Auth, Logging
from src.core.configs.bot import Bot
from src.core.configs.database import Database
from src.core.configs.dev import Dev
from src.core.configs.infrastructure import S3, MLService, Redis

if __name__ == "__main__":
	import sys

	BASE_DIR = Path(__file__).parent.parent.parent.parent
	sys.path.append(str(BASE_DIR))

BASE_DIR = Path(__file__).parent.parent.parent.parent
ENV_PATH = BASE_DIR.joinpath(".env")
JSON_SETTINGS_PATH = BASE_DIR.joinpath("config.json")
TOML_SETTINGS_PATH = BASE_DIR.joinpath("config.toml")

PathsSourcesDict: dict[Path, type[PydanticBaseSettingsSource]] = {
	TOML_SETTINGS_PATH: TomlConfigSettingsSource,
	JSON_SETTINGS_PATH: JsonConfigSettingsSource,
	ENV_PATH: EnvSettingsSource,
}


class Config(BaseSettings):
	model_config = SettingsConfigDict(
		extra="ignore",
		env_file=ENV_PATH,
		json_file=JSON_SETTINGS_PATH,
		toml_file=TOML_SETTINGS_PATH,
		env_file_encoding="utf-8",
		env_nested_delimiter="__",
		case_sensitive=False,
	)

	app: App = App()
	auth: Auth = Auth()
	bot: Bot = Bot()
	database: Database = Database()
	s3: S3 = S3()
	redis: Redis = Redis()
	ml_service: MLService = MLService()
	logging: Logging = Logging()
	dev: Dev = Dev()

	@property
	def tz(self) -> ZoneInfo:
		return ZoneInfo(self.app.tz_name)

	@classmethod
	def settings_customise_sources(
		cls,
		settings_cls: type[BaseSettings],
		init_settings: PydanticBaseSettingsSource,  # noqa: ARG003
		env_settings: PydanticBaseSettingsSource,  # noqa: ARG003
		dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
		file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003
	) -> tuple[PydanticBaseSettingsSource, ...]:
		res = [
			method(settings_cls)
			for path, method in PathsSourcesDict.items()
			if path.exists()
		]
		return EnvSettingsSource(settings_cls), *res


settings = Config()

if __name__ == "__main__":
	print(BASE_DIR)
	print(settings.model_dump_json(indent=2))
