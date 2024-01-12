# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
from craft_parts import Part, PartInfo, ProjectInfo

from snapcraft.parts.plugins import MatterPlugin

# The repository where the matter SDK resides.
MATTER_REPO = "https://github.com/project-chip/connectedhomeip.git"


@pytest.fixture(autouse=True)
def part_info(new_dir):
    yield PartInfo(
        project_info=ProjectInfo(
            application_name="test", project_name="test-snap", cache_dir=new_dir
        ),
        part=Part("my-part", {}),
    )


def test_get_build_snaps(part_info):
    properties = MatterPlugin.properties_class.unmarshal(
        {"matter-sdk-version": "master", "matter-zap-version": "v2023.11.13"}
    )
    plugin = MatterPlugin(properties=properties, part_info=part_info)
    assert plugin.get_build_snaps() == set()


def test_get_build_packages(part_info):
    properties = MatterPlugin.properties_class.unmarshal(
        {"matter-sdk-version": "master", "matter-zap-version": "v2023.11.13"}
    )
    plugin = MatterPlugin(properties=properties, part_info=part_info)
    assert plugin.get_build_packages() == {
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


def test_get_build_environment(part_info):
    properties = MatterPlugin.properties_class.unmarshal(
        {"matter-sdk-version": "master", "matter-zap-version": "v2023.11.13"}
    )
    plugin = MatterPlugin(properties=properties, part_info=part_info)

    assert plugin.get_build_environment() == {}


def test_get_build_commands(part_info):
    properties = MatterPlugin.properties_class.unmarshal(
        {"matter-sdk-version": "master", "matter-zap-version": "v2023.11.13"}
    )
    plugin = MatterPlugin(properties=properties, part_info=part_info)

    expected_commands = []

    if plugin.snap_arch == "arm64":
        expected_commands.extend(
            [
                f"wget --no-verbose https://github.com/project-chip/zap/releases/download/"
                f"{properties.matter_zap_version}/zap-linux-arm64.zip",
                "unzip -o zap-linux-arm64.zip",
                "echo 'export ZAP_INSTALL_PATH=$PWD'",
            ]
        )

    expected_commands.extend(
        [
            "if [ ! -d matter ]; then",
            f"    git clone --depth 1 -b {properties.matter_sdk_version} {MATTER_REPO} matter;",
            "else",
            "    echo 'Matter repository already exists, skip clone';",
            "fi",
            "cd matter;",
            "scripts/checkout_submodules.py --shallow --platform linux",
            r"sed -i 's/\/tmp/\/mnt/g' src/platform/Linux/CHIPLinuxStorage.h",
            r"sed -i 's/\/tmp/\/mnt/g' src/platform/Linux/CHIPPlatformConfig.h",
            "set +u && source scripts/setup/bootstrap.sh --platform build && set -u",
            "echo 'Built Matter SDK'",
        ]
    )

    assert plugin.get_build_commands() == expected_commands
