"""
Hook module to be used by tox to ensure that setuptools version is not necessarily the latest
"""

from os import getenv

from pluggy import HookimplMarker
from tox.config import Config

hookimpl = HookimplMarker("tox")

# This will store the setuptools version specified for each testenv
PER_ENV_SETUPTOOLS_VERSIONS = {}

TOX_SETUPTOOLS_VERSION_VAR = "TOX_SETUPTOOLS_VERSION"


def get_setuptools_package_version(setuptools_version: str) -> str:
    """
    Generate the right setuptools command for pip command

    :param setuptools_version: Setuptools version obtained from
    :return: A string formatted for pip install command (e.g setuptools==58.0.0)
    """
    setuptools_version = setuptools_version.lower().strip()
    # tox.ini: setuptools_version = setuptools==19.0
    if setuptools_version.startswith("setuptools"):
        return setuptools_version
    # tox.ini: setuptools_version = 19.0
    return f"setuptools=={setuptools_version}"


@hookimpl
def tox_configure(config: Config):
    """
    Tox configure implementation

    :param config: Tox configuration
    :return: Nothing, update PER_ENV_SETUPTOOLS_VERSIONS dictionary
    """
    for env, envconfig in config.envconfigs.items():
        setuptools_version = envconfig._reader.getstring(  # pylint: disable=W0212
            "setuptools_version"
        )
        if setuptools_version:
            PER_ENV_SETUPTOOLS_VERSIONS[env] = setuptools_version


@hookimpl(tryfirst=True)
def tox_testenv_install_deps(venv, action) -> None:
    """
    tox_testenv_install_deps implementation.

    Forces installation of setuptools with a specific version
    :param venv: Virtualenv object
    :param action: Action to run
    :return: Nothing, update current venv setup
    """

    # Grab the env this way to respect `setenv = TOX_SETUPTOOLS_VERSION`, if present.
    # But, fallback to the process-level environment if not present in `setenv`
    env = venv._get_os_environ()  # pylint: disable=W0212
    tox_setuptools_version_from_env = env.get(
        TOX_SETUPTOOLS_VERSION_VAR, getenv(TOX_SETUPTOOLS_VERSION_VAR)
    )

    # action.venvname is 'py36', for example.
    #
    # tox 3.8 changed action.venvname -> action.name, and removed action.id
    try:
        venvname = action.venvname
    except AttributeError:
        venvname = action.name

    # Use `setuptools_version` in tox.ini over the environment variable
    setuptools_version = PER_ENV_SETUPTOOLS_VERSIONS.get(
        venvname, tox_setuptools_version_from_env
    )
    if setuptools_version:
        package = get_setuptools_package_version(setuptools_version)

        # Is there a way to output this better? Genuine tox commands show up
        # colorized (as bold white text)...
        print(f"{venvname} setuptools_version is {package}")

        # "private" _install method - unstable interface?
        venv._install(  # pylint: disable=W0212
            [package], extraopts=["--upgrade"], action=action
        )
