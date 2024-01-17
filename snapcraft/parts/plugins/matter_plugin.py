# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The matter plugin."""
import os
from typing import Any, Dict, List, Set, cast

from craft_parts import infos, plugins
from overrides import overrides

# The repository where the matter SDK resides.
MATTER_REPO = "https://github.com/project-chip/connectedhomeip.git"


class MatterPluginProperties(plugins.PluginProperties, plugins.PluginModel):
    """The part properties used by the matter plugin."""

    matter_sdk_version: str
    matter_zap_version: str

    @classmethod
    @overrides
    def unmarshal(cls, data: Dict[str, Any]) -> "MatterPluginProperties":
        """Populate class attributes from the part specification.

        :param data: A dictionary containing part properties.

        :return: The populated plugin properties data object.

        :raise pydantic.ValidationError: If validation fails.
        """
        plugin_data = plugins.extract_plugin_properties(
            data,
            plugin_name="matter",
            required=["matter_sdk_version", "matter_zap_version"],
        )
        return cls(**plugin_data)


class MatterPlugin(plugins.Plugin):
    """A plugin for matter project.

    This plugin uses the common plugin keywords.
    For more information check the 'plugins' topic.

    Additionally, this plugin uses the following plugin-specific keywords:
        - matter-sdk-version
          (str, no default)
          The matter SDK version to use for the build.
        - matter-zap-version
          (str, no default)
          The zap version to use for the build.
    """

    properties_class = MatterPluginProperties

    def __init__(
        self,
        *,
        properties: plugins.PluginProperties,
        part_info: infos.PartInfo,
    ) -> None:
        super().__init__(properties=properties, part_info=part_info)

        self.matter_dir = part_info.part_build_dir
        self.snap_arch = os.getenv("SNAP_ARCH")

    @overrides
    def get_build_packages(self) -> Set[str]:
        return {
            "clang",
            "cmake",
            "generate-ninja",
            "git",
            "libavahi-client-dev",
            "libcairo2-dev",
            "libdbus-1-dev",
            "libgirepository1.0-dev",
            "libglib2.0-dev",
            "libreadline-dev",
            "libssl-dev",
            "ninja-build",
            "pkg-config",
            "python3-dev",
            "python3-pip",
            "python3-venv",
            "unzip",
            "wget",
        }

    @overrides
    def get_build_environment(self) -> Dict[str, str]:
        return {}

    @overrides
    def get_build_snaps(self) -> Set[str]:
        return set()

    @overrides
    def get_build_commands(self) -> List[str]:
        options = cast(MatterPluginProperties, self._options)
        commands = []

        if self.snap_arch == "arm64":
            commands.extend(
                [
                    f"wget --no-verbose https://github.com/project-chip/zap/releases/download/"
                    f"{options.matter_zap_version}/zap-linux-{self.snap_arch}.zip",
                    f"unzip -o zap-linux-{self.snap_arch}.zip",
                    "echo 'export ZAP_INSTALL_PATH=$PWD'",
                ]
            )

        # Clone Matter repository if not present
        commands.extend(
            [
                "if [ ! -d matter ]; then",
                f"    git clone {MATTER_REPO} matter && cd matter && git checkout {options.matter_sdk_version};",
                "else",
                "    echo 'Matter repository already exists, skip clone';",
                "    cd matter;",
                "fi",
            ]
        )

        # Checkout submodules for Linux platform
        commands.extend(["scripts/checkout_submodules.py --shallow --platform linux"])

        # The project writes its data to /tmp which isn't persisted.

        # Setting TMPDIR env var when running the app isn't sufficient as
        # chip_[config,counter,factory,kvs].ini still get written under /tmp.
        # The chip-tool currently has no way of overriding the default paths to
        # storage and security config files.

        # Snap does not allow bind mounting a persistent directory on /tmp,
        # so we need to replace it in the source with another path, e.g. /mnt.
        # See the top-level layout definition which bind mounts a persisted
        # directory within the confined snap space on /mnt.

        # Replace storage paths
        commands.extend(
            [
                r"sed -i 's/\/tmp/\/mnt/g' src/platform/Linux/CHIPLinuxStorage.h",
                r"sed -i 's/\/tmp/\/mnt/g' src/platform/Linux/CHIPPlatformConfig.h",
            ]
        )

        # Bootstrapping script for building Matter SDK with minimal "build" requirements
        # and setting up the environment.

        commands.extend(
            ["set +u && source scripts/setup/bootstrap.sh --platform build && set -u"]
        )

        commands.extend(["echo 'Built Matter SDK'"])

        return commands
