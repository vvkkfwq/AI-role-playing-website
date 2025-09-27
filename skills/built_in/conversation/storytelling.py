import random
from typing import Dict, Any, List
from datetime import datetime

from ...core.base import SkillBase
from ...core.models import (
    SkillMetadata, SkillContext, SkillConfig, SkillResult,
    SkillCategory, SkillTrigger, SkillPriority
)


class StorytellingSkill(SkillBase):
    """
    故事讲述技能 - 根据用户请求讲述相关的故事或经历
    """

    @classmethod
    def get_metadata(cls) -> SkillMetadata:
        """获取技能元数据"""
        return SkillMetadata(
            name="storytelling",
            display_name="故事讲述",
            description="讲述引人入胜的故事，分享角色的经历和冒险，激发想象力",
            category=SkillCategory.CONVERSATION,
            triggers=SkillTrigger(
                keywords=["故事", "经历", "冒险", "传说", "分享", "讲述", "曾经"],
                patterns=[r".*讲.*故事.*", r".*分享.*经历.*", r".*冒险.*", r".*传说.*"],
                intent_types=["storytelling", "roleplay"],
                emotional_states=["curious", "happy"]
            ),
            priority=SkillPriority.HIGH,
            character_compatibility=["哈利·波特", "苏格拉底", "阿尔伯特·爱因斯坦"],
            max_execution_time=20.0
        )

    def can_handle(self, context: SkillContext, config: SkillConfig) -> bool:
        """判断是否能处理当前请求"""
        user_input = context.user_input.lower()

        # 检查故事相关关键词
        story_keywords = ["故事", "经历", "冒险", "传说", "分享", "讲述", "曾经", "记得"]
        has_story_request = any(keyword in user_input for keyword in story_keywords)

        # 检查询问模式
        question_patterns = ["讲", "说", "分享", "聊聊", "谈谈"]
        has_request_pattern = any(pattern in user_input for pattern in question_patterns)

        return has_story_request or has_request_pattern

    def get_confidence_score(self, context: SkillContext, config: SkillConfig) -> float:
        """计算技能置信度"""
        user_input = context.user_input.lower()
        score = 0.0

        # 基于关键词匹配
        story_words = ["故事", "经历", "冒险", "传说", "分享", "讲述", "曾经"]
        matches = sum(1 for word in story_words if word in user_input)
        score += min(matches * 0.15, 0.5)

        # 基于角色匹配
        if context.character:
            character_name = context.character.get("name", "")
            if "哈利" in character_name:
                score += 0.3  # 哈利波特最适合讲故事
            elif character_name:
                score += 0.2  # 其他角色也可以讲故事

        # 基于意图匹配
        if context.detected_intent == "storytelling":
            score += 0.4

        # 基于请求模式
        request_patterns = ["讲", "说", "分享", "聊聊", "谈谈"]
        if any(pattern in user_input for pattern in request_patterns):
            score += 0.2

        return min(score, 1.0)

    async def execute(self, context: SkillContext, config: SkillConfig) -> SkillResult:
        """执行故事讲述技能"""
        user_input = context.user_input
        character_name = context.character.get("name", "") if context.character else ""

        # 分析故事主题
        story_theme = self._analyze_story_theme(user_input)

        # 根据角色生成故事
        if "哈利" in character_name:
            story = self._generate_harry_potter_story(story_theme, context)
        elif "苏格拉底" in character_name:
            story = self._generate_socrates_story(story_theme, context)
        elif "爱因斯坦" in character_name:
            story = self._generate_einstein_story(story_theme, context)
        else:
            story = self._generate_general_story(story_theme, context)

        # 计算质量指标
        quality_score = self._calculate_quality_score(story, user_input)
        relevance_score = self._calculate_relevance_score(story, user_input, context)

        return SkillResult(
            skill_name=self.metadata.name,
            execution_id="",
            status="completed",
            generated_content=story,
            confidence_score=self.get_confidence_score(context, config),
            relevance_score=relevance_score,
            quality_score=quality_score,
            result_data={
                "story_theme": story_theme,
                "character_style": character_name,
                "word_count": len(story),
                "estimated_reading_time": len(story) // 200  # 大约每分钟200字
            }
        )

    def _analyze_story_theme(self, user_input: str) -> str:
        """分析用户想听的故事主题"""
        user_input_lower = user_input.lower()

        # 魔法/冒险主题
        if any(word in user_input_lower for word in ["魔法", "冒险", "战斗", "怪物", "魁地奇"]):
            return "adventure"

        # 友谊/成长主题
        if any(word in user_input_lower for word in ["朋友", "友谊", "成长", "学校", "同学"]):
            return "friendship"

        # 智慧/哲学主题
        if any(word in user_input_lower for word in ["智慧", "思考", "哲学", "道理", "真理"]):
            return "wisdom"

        # 科学/发现主题
        if any(word in user_input_lower for word in ["科学", "发现", "实验", "理论", "研究"]):
            return "discovery"

        # 挑战/困难主题
        if any(word in user_input_lower for word in ["困难", "挑战", "问题", "解决", "克服"]):
            return "challenge"

        # 回忆/经历主题
        if any(word in user_input_lower for word in ["回忆", "以前", "小时候", "曾经", "过去"]):
            return "memory"

        return "general"

    def _generate_harry_potter_story(self, theme: str, context: SkillContext) -> str:
        """生成哈利波特风格的故事"""
        stories = {
            "adventure": [
                "我想起那次在禁林的冒险。当时我和赫敏、罗恩被德拉科告发，不得不在午夜去禁林做护树。起初我们都很害怕，但当我遇到那只独角兽时，我意识到有些东西比恐惧更重要。虽然我们面临着神秘人的威胁，但我学会了勇气不是没有恐惧，而是尽管恐惧仍然去做正确的事。",
                "有一次魁地奇比赛，我的飞天扫帚突然失控。当时整个体育场的人都在看着我，我感到非常无助。但是赫敏发现了真相——奇洛教授在念咒语控制我的扫帚。这次经历让我明白，有时候我们面临的困难并不是偶然的，而是有人故意制造的。但只要有朋友的帮助，没有什么是不能克服的。"
            ],
            "friendship": [
                "我永远不会忘记第一次遇到罗恩和赫敏的那一天。在霍格沃茨特快上，罗恩帮我找巧克力蛙卡片，虽然他家境不富裕，但他分享了他仅有的食物。而赫敏，她起初显得有些傲慢，但当我们一起对抗巨怪时，我们成为了真正的朋友。友谊不是因为我们相似，而是因为我们愿意为彼此承担。",
                "在魔法石的冒险中，我意识到朋友的重要性。赫敏用她的智慧解决了魔药的谜题，罗恩在巫师棋中勇敢地牺牲自己。如果没有他们，我永远无法到达魔法石。真正的友谊就是这样——每个人都有自己的长处，而当我们团结在一起时，就没有什么是不可能的。"
            ],
            "wisdom": [
                "邓布利多校长曾经告诉我一句话：'沉湎于虚幻的梦想，而忘记现实的生活，这是毫无益处的。'这句话在我面对厄里斯魔镜时特别有意义。魔镜让我看到了和父母在一起的画面，我几乎沉迷其中。但邓布利多的话提醒我，生活在现实中，为了目标而努力，比沉浸在不可能的幻想中更重要。",
                "有一次我问邓布利多为什么伏地魔无法杀死我，他说这是因为我母亲的爱。起初我不理解，但后来我明白了——爱是最强大的魔法，它可以保护我们，也可以让我们变得强大。不是我有什么特殊的力量，而是我被爱保护着，这让我有勇气面对任何困难。"
            ],
            "challenge": [
                "每次面对伏地魔时，我都感到恐惧，但我学会了接受这种恐惧。在墓地重生仪式上，我眼睁睁看着塞德里克被杀害，那一刻我想要逃跑。但我意识到，如果我不站出来对抗邪恶，还会有更多无辜的人受害。有时候，做正确的事并不意味着我们不害怕，而是即使害怕也要坚持下去。",
                "三强争霸赛中的每一个任务都让我成长。火龙、湖底救人、迷宫中的危险——每一次我都觉得自己不够强大。但我发现，真正的勇气不是没有恐惧，而是在恐惧中仍然选择做正确的事。每一次挑战都让我变得更强，不是因为魔法，而是因为我学会了相信自己。"
            ],
            "memory": [
                "我常常想起我的父母，虽然我对他们的记忆很少。但通过朋友和老师的讲述，我了解到他们是多么勇敢和善良的人。他们为了保护我而牺牲，这份爱一直伴随着我。虽然我从小就是孤儿，但我从来不是真正孤独的，因为爱从未离开过我。",
                "在霍格沃茨的每一天都是珍贵的回忆。从第一次踏进大礼堂的震撼，到学会第一个魔咒的兴奋，再到和朋友们一起度过的每一个节日。这些回忆让我明白，家不是一个地方，而是和那些关心你的人在一起的感觉。霍格沃茨就是我的家。"
            ]
        }

        story_list = stories.get(theme, stories["adventure"])
        selected_story = random.choice(story_list)

        return f"让我来分享一个我的经历...\n\n{selected_story}\n\n这就是我想告诉你的故事。每个人的人生都充满了冒险和成长，重要的是我们从中学到什么，以及我们如何用这些经历帮助他人。"

    def _generate_socrates_story(self, theme: str, context: SkillContext) -> str:
        """生成苏格拉底风格的故事"""
        stories = {
            "wisdom": [
                "让我给你讲一个关于智慧的故事。有一天，德尔斐神谕说我是雅典最聪明的人。我感到困惑，因为我知道自己其实一无所知。于是我去拜访那些被认为聪明的人——政治家、诗人、工匠。我发现他们虽然在各自领域有专长，但都认为自己无所不知。而我呢？我知道自己的无知。也许这就是神谕的意思——真正的智慧在于认识到自己的无知。",
                "有一次，一个年轻人问我什么是勇气。我没有直接回答，而是问他：'你见过勇敢的士兵吗？''是的，'他说，'他们在战场上不怕死。''那么，'我又问，'一个人仅仅因为不怕死就是勇敢的吗？如果一个疯子不怕死，他也是勇敢的吗？'通过这样的对话，我们一起发现了勇气的真正含义——不是无知无畏，而是明知危险仍选择做正确的事。"
            ],
            "challenge": [
                "当我被控腐蚀青年和不信神时，我可以选择逃离雅典或者改变我的哲学观点。但我选择了留下来面对审判。我的朋友们问我为什么不为自己辩护，我告诉他们：如果我为了活命而放弃我的使命，那我还算什么哲学家？一个人的价值不在于活多久，而在于如何活。即使面对死亡，我也要坚持我的原则。",
                "有一天，一个富商向我抱怨说他的儿子不听话，浪费金钱。我问他：'你花了多少时间教导他金钱的价值？''我很忙，'他说，'我把他交给了最好的老师。''那么，'我说，'你认为品德可以像商品一样买卖吗？'最终我们都明白了，真正的教育需要的是父母的关爱和以身作则，而不是金钱。"
            ],
            "friendship": [
                "我有一个朋友叫克里同，他是个善良的人，总是担心我的安全。当我被判死刑时，他来到狱中要帮我越狱。他说：'苏格拉底，你不能死，你的朋友们需要你！'我被他的友谊感动，但我问他：'如果我逃跑了，我不是在教导人们可以违背法律吗？真正的友谊是支持朋友做正确的事，还是帮助朋友逃避责任？'最终，他理解了我的选择。",
                "年轻时，我有许多追随者，他们认为跟随我就能获得智慧。但我告诉他们，我不是他们的老师，而是他们的朋友。我的作用是帮助他们发现自己内心已经拥有的智慧。真正的友谊不是依赖，而是互相启发，一起寻求真理。"
            ]
        }

        story_list = stories.get(theme, stories["wisdom"])
        selected_story = random.choice(story_list)

        return f"让我分享一个关于人生的思考...\n\n{selected_story}\n\n这个故事让你想到了什么？你认为其中蕴含着什么道理？有时候，故事的价值不在于故事本身，而在于它引发的思考。"

    def _generate_einstein_story(self, theme: str, context: SkillContext) -> str:
        """生成爱因斯坦风格的故事"""
        stories = {
            "discovery": [
                "我想起我提出相对论的那段时间。当时我在专利局工作，每天审查各种发明。有一天，我在想象如果我能够以光速运动会看到什么。这个简单的思想实验最终导致了狭义相对论的诞生。科学就是这样，最伟大的发现往往来自最简单的好奇心。我们不需要复杂的设备，只需要一个愿意思考的大脑。",
                "布朗运动的发现给了我很大启发。看着显微镜下花粉的随机运动，我意识到这证明了原子的存在。许多人认为这只是一个有趣的观察，但我看到了其中的深刻含义。这让我明白，大自然总是在最微小的细节中隐藏着最伟大的秘密。"
            ],
            "challenge": [
                "当我提出广义相对论时，几乎没有人相信我。牛顿的理论已经统治了几个世纪，人们很难接受时空会弯曲的想法。但我相信数学和逻辑，即使整个世界都反对我。1919年的日食观测证实了我的理论，那一刻我并不感到意外，因为我知道真理总会胜利。坚持自己的信念，即使在孤独中，也是科学家必须具备的品质。",
                "在纳粹统治德国时，我的理论被称为'犹太物理学'而遭到攻击。我可以选择保持沉默，但我选择了发声。科学没有种族，真理没有国界。一个科学家的责任不仅是发现真理，更要为真理而战，为人类的尊严而战。"
            ],
            "wisdom": [
                "有人问我宇宙最强大的力量是什么，我说是复利。但开玩笑之后，我认真地说，是人类的好奇心和想象力。知识给我们工具，但想象力给我们翅膀。我的理论不是从实验室来的，而是从我的想象来的。当我们停止好奇，停止想象，我们就停止了成长。",
                "我常常思考上帝是否掷骰子这个问题。虽然我在量子力学上与波尔有分歧，但这种科学辩论是珍贵的。真理不是通过权威获得的，而是通过理性的辩论和实验验证获得的。保持开放的心态，勇于质疑，这是通向智慧的道路。"
            ]
        }

        story_list = stories.get(theme, stories["discovery"])
        selected_story = random.choice(story_list)

        return f"让我告诉你一个科学发现的故事...\n\n{selected_story}\n\n你知道吗？科学最美妙的地方在于，每一个答案都会带来更多的问题。这就是人类永远在进步的原因。好奇心是我们最宝贵的财富。"

    def _generate_general_story(self, theme: str, context: SkillContext) -> str:
        """生成通用故事"""
        stories = {
            "general": [
                "让我给你讲一个小故事。从前有一个人在路上丢了钥匙，他在路灯下找来找去。路人问他：'你确定钥匙是在这里丢的吗？'他说：'不是，但是只有这里有光。'这个故事让我们思考：我们是否经常在舒适区里寻找答案，而忽略了真正需要去的地方？",
                "有一个古老的寓言：一只青蛙掉进了一口井里。经过努力，它终于跳了出来。当它向别的青蛙讲述外面世界的广阔时，井里的青蛙们都不相信。有时候，我们的视野被我们的经历所限制。保持开放的心态，相信还有更大的世界等待我们去发现。"
            ]
        }

        story_list = stories.get(theme, stories["general"])
        selected_story = random.choice(story_list)

        return f"{selected_story}\n\n每个故事都有它的道理，每个人也会从中得到不同的启发。你从这个故事中想到了什么？"

    def _calculate_quality_score(self, story: str, user_input: str) -> float:
        """计算故事质量得分"""
        score = 0.0

        # 基于长度
        length = len(story)
        if 200 <= length <= 600:
            score += 0.3
        elif length > 600:
            score += 0.2

        # 基于叙事结构
        if "让我" in story or "我想起" in story or "有一次" in story:
            score += 0.2

        # 基于是否有深度
        depth_indicators = ["明白", "学会", "理解", "发现", "意识到"]
        if any(indicator in story for indicator in depth_indicators):
            score += 0.3

        # 基于是否有对话感
        if "你" in story and ("吗" in story or "呢" in story):
            score += 0.2

        return min(score, 1.0)

    def _calculate_relevance_score(self, story: str, user_input: str, context: SkillContext) -> float:
        """计算相关性得分"""
        score = 0.7  # 基础得分

        # 检查主题相关性
        user_words = set(user_input.lower().split())
        story_words = set(story.lower().split())
        overlap = len(user_words.intersection(story_words))
        if overlap > 0:
            score += min(overlap * 0.05, 0.2)

        # 检查意图匹配
        if context.detected_intent == "storytelling":
            score += 0.1

        return min(score, 1.0)