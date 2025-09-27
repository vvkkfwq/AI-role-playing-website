import os
import importlib
import inspect
from typing import Dict, List, Type, Optional, Set, Any
from pathlib import Path
import logging

from .base import SkillBase
from .models import SkillMetadata, SkillCategory

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    技能注册中心 - 使用工厂模式管理技能的发现、注册和创建
    """

    def __init__(self):
        self._skills: Dict[str, Type[SkillBase]] = {}
        self._metadata: Dict[str, SkillMetadata] = {}
        self._skill_instances: Dict[str, SkillBase] = {}
        self._categories: Dict[SkillCategory, List[str]] = {
            category: [] for category in SkillCategory
        }
        self._dependencies: Dict[str, Set[str]] = {}

    def register_skill(
        self,
        skill_class: Type[SkillBase],
        metadata: Optional[SkillMetadata] = None
    ) -> bool:
        """
        注册技能类

        Args:
            skill_class: 技能类
            metadata: 技能元数据，如果为None则从类中获取

        Returns:
            bool: 注册是否成功
        """
        try:
            # 获取技能元数据
            if metadata is None:
                if hasattr(skill_class, 'get_metadata'):
                    metadata = skill_class.get_metadata()
                else:
                    raise ValueError(f"技能类 {skill_class.__name__} 必须提供metadata或实现get_metadata方法")

            skill_name = metadata.name

            # 检查是否已注册
            if skill_name in self._skills:
                logger.warning(f"技能 '{skill_name}' 已存在，将被覆盖")

            # 验证技能类
            if not issubclass(skill_class, SkillBase):
                raise ValueError(f"技能类 {skill_class.__name__} 必须继承自SkillBase")

            # 验证元数据
            validation_errors = self._validate_metadata(metadata)
            if validation_errors:
                raise ValueError(f"技能元数据验证失败: {', '.join(validation_errors)}")

            # 注册技能
            self._skills[skill_name] = skill_class
            self._metadata[skill_name] = metadata

            # 更新分类索引
            if skill_name not in self._categories[metadata.category]:
                self._categories[metadata.category].append(skill_name)

            # 处理依赖关系
            self._dependencies[skill_name] = set(metadata.dependencies)

            logger.info(f"成功注册技能: {skill_name} ({metadata.category})")
            return True

        except Exception as e:
            logger.error(f"注册技能失败 {skill_class.__name__}: {e}")
            return False

    def unregister_skill(self, skill_name: str) -> bool:
        """
        注销技能

        Args:
            skill_name: 技能名称

        Returns:
            bool: 注销是否成功
        """
        try:
            if skill_name not in self._skills:
                logger.warning(f"技能 '{skill_name}' 不存在")
                return False

            # 检查是否有其他技能依赖此技能
            dependent_skills = [
                name for name, deps in self._dependencies.items()
                if skill_name in deps and name != skill_name
            ]

            if dependent_skills:
                logger.error(f"无法注销技能 '{skill_name}'，因为它被以下技能依赖: {dependent_skills}")
                return False

            # 获取元数据
            metadata = self._metadata[skill_name]

            # 移除注册信息
            del self._skills[skill_name]
            del self._metadata[skill_name]

            # 移除实例
            if skill_name in self._skill_instances:
                del self._skill_instances[skill_name]

            # 更新分类索引
            if skill_name in self._categories[metadata.category]:
                self._categories[metadata.category].remove(skill_name)

            # 移除依赖关系
            if skill_name in self._dependencies:
                del self._dependencies[skill_name]

            logger.info(f"成功注销技能: {skill_name}")
            return True

        except Exception as e:
            logger.error(f"注销技能失败 {skill_name}: {e}")
            return False

    def get_skill(self, skill_name: str) -> Optional[SkillBase]:
        """
        获取技能实例

        Args:
            skill_name: 技能名称

        Returns:
            Optional[SkillBase]: 技能实例，如果不存在则返回None
        """
        if skill_name not in self._skills:
            logger.warning(f"技能 '{skill_name}' 未注册")
            return None

        # 使用单例模式，确保每个技能只有一个实例
        if skill_name not in self._skill_instances:
            try:
                skill_class = self._skills[skill_name]
                metadata = self._metadata[skill_name]
                skill_instance = skill_class(metadata)
                self._skill_instances[skill_name] = skill_instance
                logger.debug(f"创建技能实例: {skill_name}")
            except Exception as e:
                logger.error(f"创建技能实例失败 {skill_name}: {e}")
                return None

        return self._skill_instances[skill_name]

    def get_skills_by_category(self, category: SkillCategory) -> List[SkillBase]:
        """
        根据分类获取技能列表

        Args:
            category: 技能分类

        Returns:
            List[SkillBase]: 技能实例列表
        """
        skill_names = self._categories.get(category, [])
        skills = []

        for name in skill_names:
            skill = self.get_skill(name)
            if skill:
                skills.append(skill)

        return skills

    def get_available_skills(self, character_name: Optional[str] = None) -> List[SkillBase]:
        """
        获取可用技能列表

        Args:
            character_name: 角色名称，用于过滤兼容的技能

        Returns:
            List[SkillBase]: 可用技能列表
        """
        skills = []

        for skill_name, metadata in self._metadata.items():
            # 检查技能是否启用
            if not metadata.enabled:
                continue

            # 检查角色兼容性
            if character_name and metadata.character_compatibility:
                if character_name not in metadata.character_compatibility:
                    continue

            # 检查依赖关系
            if not self._check_dependencies(skill_name):
                continue

            skill = self.get_skill(skill_name)
            if skill:
                skills.append(skill)

        return skills

    def get_skill_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """
        获取技能元数据

        Args:
            skill_name: 技能名称

        Returns:
            Optional[SkillMetadata]: 技能元数据
        """
        return self._metadata.get(skill_name)

    def list_skills(self) -> List[str]:
        """
        列出所有已注册的技能名称

        Returns:
            List[str]: 技能名称列表
        """
        return list(self._skills.keys())

    def auto_discover_skills(self, skill_dirs: List[str]):
        """
        自动发现并注册技能

        Args:
            skill_dirs: 技能目录列表
        """
        discovered_count = 0

        for skill_dir in skill_dirs:
            try:
                discovered_count += self._discover_skills_in_directory(skill_dir)
            except Exception as e:
                logger.error(f"在目录 '{skill_dir}' 中发现技能失败: {e}")

        logger.info(f"自动发现完成，共发现 {discovered_count} 个技能")

    def _discover_skills_in_directory(self, skill_dir: str) -> int:
        """
        在指定目录中发现技能

        Args:
            skill_dir: 技能目录

        Returns:
            int: 发现的技能数量
        """
        discovered_count = 0
        skill_path = Path(skill_dir)

        if not skill_path.exists() or not skill_path.is_dir():
            logger.warning(f"技能目录不存在或不是目录: {skill_dir}")
            return 0

        # 遍历Python文件
        for py_file in skill_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                # 构建模块路径
                relative_path = py_file.relative_to(skill_path.parent)
                module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")

                # 导入模块
                module = importlib.import_module(module_path)

                # 查找技能类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, SkillBase) and
                        obj != SkillBase and
                        hasattr(obj, 'get_metadata')):

                        try:
                            metadata = obj.get_metadata()
                            if self.register_skill(obj, metadata):
                                discovered_count += 1
                                logger.debug(f"自动发现技能: {metadata.name} 来自 {py_file}")
                        except Exception as e:
                            logger.warning(f"注册自动发现的技能失败 {name}: {e}")

            except Exception as e:
                logger.warning(f"加载技能文件失败 {py_file}: {e}")

        return discovered_count

    def _validate_metadata(self, metadata: SkillMetadata) -> List[str]:
        """
        验证技能元数据

        Args:
            metadata: 技能元数据

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        # 基本字段验证
        if not metadata.name or not metadata.name.strip():
            errors.append("技能名称不能为空")

        if not metadata.display_name or not metadata.display_name.strip():
            errors.append("显示名称不能为空")

        if not metadata.description or not metadata.description.strip():
            errors.append("技能描述不能为空")

        # 版本格式验证（简单检查）
        if not metadata.version or "." not in metadata.version:
            errors.append("版本格式无效")

        # 性能配置验证
        if metadata.max_execution_time <= 0:
            errors.append("最大执行时间必须大于0")

        if metadata.concurrent_limit <= 0:
            errors.append("并发限制必须大于0")

        return errors

    def _check_dependencies(self, skill_name: str) -> bool:
        """
        检查技能依赖关系是否满足

        Args:
            skill_name: 技能名称

        Returns:
            bool: 依赖关系是否满足
        """
        dependencies = self._dependencies.get(skill_name, set())

        for dep in dependencies:
            if dep not in self._skills:
                logger.warning(f"技能 '{skill_name}' 的依赖 '{dep}' 未注册")
                return False

            # 检查依赖的技能是否启用
            dep_metadata = self._metadata.get(dep)
            if dep_metadata and not dep_metadata.enabled:
                logger.warning(f"技能 '{skill_name}' 的依赖 '{dep}' 已禁用")
                return False

        return True

    def get_skill_graph(self) -> Dict[str, List[str]]:
        """
        获取技能依赖图

        Returns:
            Dict[str, List[str]]: 技能依赖关系图
        """
        return {
            skill_name: list(deps)
            for skill_name, deps in self._dependencies.items()
        }

    def validate_skill_dependencies(self) -> Dict[str, List[str]]:
        """
        验证所有技能的依赖关系

        Returns:
            Dict[str, List[str]]: 验证错误，键为技能名称，值为错误列表
        """
        errors = {}

        for skill_name in self._skills:
            skill_errors = []

            dependencies = self._dependencies.get(skill_name, set())
            for dep in dependencies:
                if dep not in self._skills:
                    skill_errors.append(f"依赖的技能 '{dep}' 未注册")

            if skill_errors:
                errors[skill_name] = skill_errors

        return errors

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        获取注册中心统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        category_counts = {
            category.value: len(skills)
            for category, skills in self._categories.items()
        }

        enabled_count = sum(
            1 for metadata in self._metadata.values()
            if metadata.enabled
        )

        return {
            "total_skills": len(self._skills),
            "enabled_skills": enabled_count,
            "disabled_skills": len(self._skills) - enabled_count,
            "category_distribution": category_counts,
            "skills_with_dependencies": len([
                name for name, deps in self._dependencies.items()
                if deps
            ]),
            "total_dependencies": sum(len(deps) for deps in self._dependencies.values())
        }


# 全局技能注册中心实例
skill_registry = SkillRegistry()