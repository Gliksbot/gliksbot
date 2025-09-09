import os
import sys

from backend.skills.skills_manager import SkillsManager


def test_system_info_skill(tmp_path):
    manager = SkillsManager(str(tmp_path))
    result = manager.execute_skill_by_name("system_info", "hello")
    assert result["success"] is True
    assert result["platform"] == sys.platform
    assert result["cwd"] == os.getcwd()
    assert result["python_version"] == sys.version

