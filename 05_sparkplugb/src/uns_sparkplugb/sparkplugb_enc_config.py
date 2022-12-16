from dynaconf import Dynaconf
import os

current_folder = os.path.dirname(os.path.abspath(__file__))

settings = Dynaconf(
    envvar_prefix="UNS",
    root_path=current_folder,
    settings_files=['../../conf/settings.yaml', '../../conf/.secrets.yaml'],
)

# `envvar_prefix` = export envvars with `export UNS_FOO=bar`.
# `settings_files` = Load these files in the order.
