"""SkillFather 安装器模块 —— 将 SkillFather 注册为 WorkBuddy 本地 Skill。

支持两种调用方式：
1. CLI 子命令: ``skillfather install-skill``
2. ``setup.py`` 后置安装钩子（pip install 完成后自动触发）

安装逻辑：定位 SKILL.md 模板 -> 复制到 ~/.workbuddy/skills/skillfather/ -> 完成
"""

import shutil
import sys
from pathlib import Path

# WorkBuddy Skills 的标准安装路径
WORKBUDDY_SKILLS_DIR = Path.home() / ".workbuddy" / "skills"
TARGET_DIR = WORKBUDDY_SKILLS_DIR / "skillfather"
TARGET_FILE = TARGET_DIR / "SKILL.md"


def _find_skill_md() -> Path | None:
    """定位 SKILL.md 模板文件。

    按优先级依次尝试以下路径：
    1. importlib.resources —— 适用于 pip install .（非 editable）安装
    2. 项目根目录 —— 适用于 pip install -e .（editable）安装
    3. 当前工作目录 —— 适用于在项目根目录下直接运行的场景

    Returns:
        SKILL.md 的 Path 对象，如果所有路径都找不到则返回 None
    """
    # 路径 1：importlib.resources（包内 data 目录，随 pip 分发）
    try:
        import importlib.resources as ir
        try:
            # Python 3.9+ API
            ref = ir.files("skillfather.data") / "SKILL.md"
            if ref.is_file():
                return Path(str(ref))
        except (FileNotFoundError, AttributeError, ModuleNotFoundError):
            pass
    except ImportError:
        pass

    # 路径 2：项目根目录（editable install 时，源码就在原位）
    # installer.py -> skillfather/ -> src/ -> 项目根目录
    project_root = Path(__file__).resolve().parent.parent.parent
    skill_md = project_root / "SKILL.md"
    if skill_md.is_file():
        return skill_md

    # 路径 3：当前工作目录
    cwd_skill = Path.cwd() / "SKILL.md"
    if cwd_skill.is_file():
        return cwd_skill

    return None


def install_skill(force: bool = False) -> bool:
    """将 SkillFather 的 SKILL.md 安装到 WorkBuddy Skills 目录。

    Args:
        force: 如果目标已存在，是否强制覆盖。默认 False（跳过并提示）。

    Returns:
        True 表示安装成功，False 表示跳过或失败
    """
    # 1. 定位模板文件
    source = _find_skill_md()
    if source is None:
        print("  [ERROR] 未找到 SKILL.md 模板文件。", file=sys.stderr)
        print("  请确保通过 pip install 安装，或在项目根目录下运行。", file=sys.stderr)
        return False

    # 2. 检测冲突（目标已存在且未指定 force）
    if TARGET_FILE.exists() and not force:
        print(f"  [SKIP] 已存在: {TARGET_FILE}")
        print(f"  如需覆盖，请运行: skillfather install-skill --force")
        return False

    # 3. 创建目标目录
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # 4. 复制文件
    shutil.copy2(source, TARGET_FILE)

    # 5. 输出成功信息
    print(f"  [OK] SkillFather Skill 已安装到: {TARGET_FILE}")
    print(f"  现在可以在 WorkBuddy 中通过 @skill:skillfather 调用。")
    return True


def uninstall_skill() -> bool:
    """卸载 WorkBuddy 中的 SkillFather Skill。

    Returns:
        True 表示卸载成功，False 表示未安装
    """
    if not TARGET_FILE.exists():
        print(f"  [SKIP] 未安装: {TARGET_FILE}")
        return False

    TARGET_FILE.unlink()
    # 如果目录为空，一并清理
    try:
        if TARGET_DIR.exists() and not any(TARGET_DIR.iterdir()):
            TARGET_DIR.rmdir()
    except OSError:
        pass  # 目录非空或其他进程占用，忽略

    print(f"  [OK] SkillFather Skill 已卸载。")
    return True
