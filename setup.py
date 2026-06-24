"""SkillFather setup.py —— 在 pyproject.toml 基础上添加后置安装钩子。

功能：
  pip install -e .  完成后 -> develop 命令钩子 -> 交互提示是否安装为 WorkBuddy Skill
  pip install .     完成后 -> install 命令钩子 -> 交互提示是否安装为 WorkBuddy Skill

所有构建配置仍在 pyproject.toml 中，此文件仅用于 cmdclass 扩展。
"""

import sys
from setuptools import setup
from setuptools.command.develop import develop as _develop
from setuptools.command.install import install as _install


def _post_install_hook():
    """pip install 完成后的交互提示。

    检测是否在交互式终端中运行，如果是则询问用户是否要安装为 WorkBuddy 本地 Skill。
    非交互环境（如 CI）下仅打印提示信息，不执行安装。
    """
    try:
        if not sys.stdin.isatty():
            # 非交互环境（CI、管道等），仅打印提示
            print()
            print("  SkillFather 安装完成！")
            print("  提示: 运行 `skillfather install-skill` 可安装为 WorkBuddy 本地 Skill。")
            print()
            return

        # 交互环境，询问用户
        print()
        print("  ╔════════════════════════════════════════════════╗")
        print("  ║  SkillFather 安装完成！                        ║")
        print("  ╚════════════════════════════════════════════════╝")
        print()
        response = input("  是否要安装为 WorkBuddy 本地 Skill? [Y/n]: ").strip().lower()

        if response in ("", "y", "yes", "是"):
            # 调用 installer 模块执行安装
            try:
                from skillfather.installer import install_skill
                ok = install_skill(force=True)
                if not ok:
                    print("  安装未完成，稍后可运行: skillfather install-skill")
            except Exception as e:
                print(f"  自动安装失败: {e}")
                print("  稍后可运行: skillfather install-skill")
        else:
            print("  跳过。稍后可运行: skillfather install-skill")
        print()
    except Exception as e:
        # 任何异常都不应阻断安装流程
        print(f"  [提示] 运行 `skillfather install-skill` 可安装为 WorkBuddy 本地 Skill。")
        print(f"  (自动安装跳过: {e})")


class develop(_develop):
    """editable install (pip install -e .) 的自定义 develop 命令。"""

    def run(self):
        super().run()
        _post_install_hook()


class install(_install):
    """regular install (pip install .) 的自定义 install 命令。"""

    def run(self):
        super().run()
        _post_install_hook()


# 所有构建配置来自 pyproject.toml，此处仅注册 cmdclass
setup(
    cmdclass={
        "develop": develop,
        "install": install,
    },
)
