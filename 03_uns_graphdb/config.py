
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="UNS",
    settings_files=['settings.yaml', '.secrets.yaml'],
)

# `envvar_prefix` = export envvars with `export UNS_FOO=bar`.
# `settings_files` = Load these files in the order.
