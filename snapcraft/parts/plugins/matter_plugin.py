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

    # part properties required by the plugin

    @classmethod
    @overrides
    def unmarshal(cls, data: Dict[str, Any]) -> "MatterPluginProperties":
        plugin_data = plugins.extract_plugin_properties(
            data, 
            plugin_name="matter", 
            # required=["zap_version_test"]
        )
        return cls(**plugin_data)


class MatterPlugin(plugins.Plugin):
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
            "wget",
            "unzip",
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

    @overrides
    def get_build_snaps(self) -> Set[str]:
        return set()

    # def _get_setup_matter(self, options) -> List[str]:
    #     return []

    @overrides
    def get_build_commands(self) -> List[str]:
        if self.snap_arch == "arm64":
            return [
                f"wget --no-verbose https://github.com/project-chip/zap/releases/download/v2023.11.13/zap-linux-{self.snap_arch}.zip",
                f"unzip -o zap-linux-{self.snap_arch}.zip",
                "echo 'export ZAP_INSTALL_PATH=$PWD'"
            ]
        return [
            f"if [ ! -d matter ]; then git clone --depth 1 -b v1.2.0.1 {MATTER_REPO} matter; fi",
            "cd matter || echo 'skip clone'",
            f"scripts/checkout_submodules.py --shallow --platform linux",
            f"set +u && source scripts/activate.sh && set -u",
            "cp -vr ./* $CRAFT_PART_INSTALL/",
            "echo 'Cloned Matter repository and activated submodules'"
        ]

        
    

