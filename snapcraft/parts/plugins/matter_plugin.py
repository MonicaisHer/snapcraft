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

from typing import Any, Dict, List, Literal, Set, cast

from craft_parts import infos, plugins
from overrides import overrides

MATTER_REPO = "https://github.com/project-chip/connectedhomeip.git"
"""The repository where the matter SDK resides."""


class MatterPluginProperties(plugins.PluginProperties, plugins.PluginModel):
    """The part properties used by the matter plugin."""

    # part properties required by the plugin
    matter_branch: str
    zap_version: str
    source: str

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
            required=["source","matter_branch","zap_version"]
        )
        return cls(**plugin_data)


class MatterPluginDependencyZap:

    def __init__(self, zap_version: str):
        self.zap_version = zap_version
        self.snap_arch = os.getenv("SNAP_ARCH")

    def build_environment(self) -> Dict[str, str]:
        environment = {}

        if self.snap_arch == "arm64":
            environment["ZAP_VERSION"] = self.zap_version

        return environment

    def build_packages(self) -> List[str]:
        return ["wget", "unzip"]

    def get_build_commands(self) -> str:
        if self.snap_arch == "arm64":
            return (
                f"wget --no-verbose https://github.com/project-chip/zap/releases/download/{self.zap_version}/zap-linux-{self.snap_arch}.zip\n"
                f"unzip -o zap-linux-{self.snap_arch}.zip\n"
                f"echo 'export ZAP_INSTALL_PATH=$PWD'"
            )
        return ""


class MatterPlugin(plugins.Plugin):
    """A plugin for matter projects.

    This plugin uses the common plugin keywords as well as those for "sources".
    For more information check the 'plugins' topic for the former and the
    'sources' topic for the latter.

    Additionally, this plugin uses the following plugin-specific keywords:
        - matter_branch
          (str: default: None)
          which branch of Matter to downlad (e.g. "v1.2.0.1")
    """

    properties_class = MatterPluginProperties

    def __init__(
        self,
        *,
        properties: plugins.PluginProperties,
        part_info: infos.PartInfo,
        zap_dependency: MatterPluginDependencyZap,
    ) -> None:
        super().__init__(properties=properties, part_info=part_info)

        self.matter_dir = part_info.part_build_dir
        self.zap_install_path = zap_dependency.override_build()

    @overrides
    def get_build_snaps(self) -> Set[str]:
        return set()

    @overrides
    def get_build_packages(self) -> Set[str]:
        return {
            "clang",
            "pkg-config",
            "git",
            "cmake",
            "ninja-build",
            "unzip",
            "libssl-dev",
            "libdbus-1-dev",
            "libglib2.0-dev",
            "libavahi-client-dev",
            "python3-venv",
            "python3-dev",
            "python3-pip",
            "libgirepository1.0-dev",
            "libcairo2-dev",
            "libreadline-dev",
            "generate-ninja",
        }

    @overrides
    def get_build_environment(self) -> Dict[str, str]:
        return {}

    def _get_setup_matter(self, options) -> List[str]:
        return [
            f"git clone --depth 1 -b {self.options.matter_branch} {MATTER_REPO} {self.matter_dir}",
            "scripts/checkout_submodules.py --shallow --platform linux",
            "source scripts/activate.sh",
        ]


