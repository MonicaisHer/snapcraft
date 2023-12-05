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
from typing import Any, Dict, List, Literal, Set, cast

from craft_parts import infos, plugins
from overrides import overrides

MATTER_REPO = "https://github.com/project-chip/connectedhomeip.git"
"""The repository where the matter SDK resides."""


class MatterPluginProperties(plugins.PluginProperties, plugins.PluginModel):
    """The part properties used by the matter plugin."""

    source: str
    matter_channel: Literal["v1.2.0.1", "v1.1.0.2", "master"] = "master"
    # matter_target: str = " "

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
            required=["source"],
        )
        return cls(**plugin_data)


class MatterPlugin(plugins.Plugin):
    """A plugin for matter projects.

    This plugin uses the common plugin keywords as well as those for "sources".
    For more information check the 'plugins' topic for the former and the
    'sources' topic for the latter.

    Additionally, this plugin uses the following plugin-specific keywords:
        - matter_channel: Literal["v1.2.0.1", "v1.1.0.2", "master"] = "master"
        - matter_target:
    """

    properties_class = MatterPluginProperties

    def __init__(
        self, *, properties: plugins.PluginProperties, part_info: infos.PartInfo
    ) -> None:
        super().__init__(properties=properties, part_info=part_info)

        self.matter_dir = part_info.part_build_dir

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
        return {
            "PATH": f"{self.matter_dir / 'bin'}:${{PATH}}",
        }

    def _get_setup_matter(self, options) -> List[str]:
        # TODO move to pull
        return [
            # TODO detect changes to plugin properties
            f"git clone --depth 1 -b {options.matter_channel} {MATTER_REPO} {self.matter_dir}",
            "scripts/checkout_submodules.py --shallow --platform linux",
            "source scripts/activate.sh",
        ]

    @overrides
    def get_build_commands(self) -> List[str]:
        options = cast(MatterPluginProperties, self._options)

        matter_install_cmd: List[str] = []

        if not self.matter_dir.exists():
            matter_install_cmd = self._get_setup_matter(options)

        matter_build_cmd = [
            f"echo {options.matter_target}",
            "echo $CRAFT_PART_INSTALL",
        ]
        return matter_install_cmd + matter_build_cmd
