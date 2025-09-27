"""
内置技能注册工具
"""

from ..core.registry import skill_registry
from ..core.models import SkillConfig

# 导入所有内置技能
from .conversation.deep_questioning import DeepQuestioningSkill
from .conversation.storytelling import StorytellingSkill
from .conversation.emotional_support import EmotionalSupportSkill
from .knowledge.analysis import AnalysisSkill


def register_built_in_skills():
    """注册所有内置技能"""

    # 注册对话类技能
    skill_registry.register_skill(DeepQuestioningSkill, DeepQuestioningSkill.get_metadata())
    skill_registry.register_skill(StorytellingSkill, StorytellingSkill.get_metadata())
    skill_registry.register_skill(EmotionalSupportSkill, EmotionalSupportSkill.get_metadata())

    # 注册知识类技能
    skill_registry.register_skill(AnalysisSkill, AnalysisSkill.get_metadata())

    print("✅ 已注册所有内置技能")


def setup_character_skill_configs():
    """设置角色技能配置"""

    character_configs = {
        # 哈利·波特的技能配置
        1: {  # 假设哈利·波特的ID为1
            "storytelling": SkillConfig(
                skill_name="storytelling",
                character_id=1,
                weight=1.5,
                threshold=0.3,
                priority="high",
                parameters={"story_style": "magical_adventure", "tone": "inspiring"},
                personalization={"magical_elements": True, "friendship_themes": True}
            ),
            "emotional_support": SkillConfig(
                skill_name="emotional_support",
                character_id=1,
                weight=1.2,
                threshold=0.4,
                parameters={"support_style": "brave_encouragement"},
                personalization={"reference_personal_struggles": True}
            ),
            "deep_questioning": SkillConfig(
                skill_name="deep_questioning",
                character_id=1,
                weight=0.8,
                threshold=0.6
            )
        },

        # 苏格拉底的技能配置
        2: {  # 假设苏格拉底的ID为2
            "deep_questioning": SkillConfig(
                skill_name="deep_questioning",
                character_id=2,
                weight=1.5,
                threshold=0.2,
                priority="critical",
                parameters={"questioning_style": "socratic_method"},
                personalization={"philosophical_depth": "high", "use_analogies": True}
            ),
            "analysis": SkillConfig(
                skill_name="analysis",
                character_id=2,
                weight=1.4,
                threshold=0.3,
                parameters={"analysis_style": "philosophical"},
                personalization={"encourage_self_reflection": True}
            ),
            "storytelling": SkillConfig(
                skill_name="storytelling",
                character_id=2,
                weight=1.0,
                threshold=0.5,
                parameters={"story_style": "philosophical_parable"}
            )
        },

        # 爱因斯坦的技能配置
        3: {  # 假设爱因斯坦的ID为3
            "analysis": SkillConfig(
                skill_name="analysis",
                character_id=3,
                weight=1.5,
                threshold=0.3,
                parameters={"analysis_style": "scientific_method"},
                personalization={"use_thought_experiments": True, "emphasize_curiosity": True}
            ),
            "storytelling": SkillConfig(
                skill_name="storytelling",
                character_id=3,
                weight=1.2,
                threshold=0.4,
                parameters={"story_style": "scientific_discovery"}
            ),
            "deep_questioning": SkillConfig(
                skill_name="deep_questioning",
                character_id=3,
                weight=1.1,
                threshold=0.4,
                parameters={"questioning_style": "scientific_inquiry"}
            )
        }
    }

    return character_configs


def initialize_skill_system():
    """初始化整个技能系统"""
    print("🚀 初始化技能系统...")

    # 注册内置技能
    register_built_in_skills()

    # 获取角色技能配置
    character_configs = setup_character_skill_configs()

    # 打印统计信息
    stats = skill_registry.get_registry_stats()
    print(f"📊 技能系统统计:")
    print(f"   - 总技能数: {stats['total_skills']}")
    print(f"   - 启用技能: {stats['enabled_skills']}")
    print(f"   - 分类分布: {stats['category_distribution']}")
    print(f"   - 角色配置: {len(character_configs)} 个角色")

    return character_configs


if __name__ == "__main__":
    initialize_skill_system()