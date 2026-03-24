import random

from models import Choice, GameState, NPC

SCENE_TEMPLATES = [
    {
        "scene": "雨夜私人会所顶层包厢",
        "event": "高净值圈层试探局",
        "atmosphere": "霓虹反光、潮湿空气、雪松与酒精气味交叠",
    },
    {
        "scene": "清晨执行董事办公室",
        "event": "并购前夜的权力博弈",
        "atmosphere": "百叶窗切割晨光、咖啡苦香、文件纸张摩擦声",
    },
    {
        "scene": "跨洋私人机舱",
        "event": "资本同盟临时谈判",
        "atmosphere": "引擎低鸣、皮革触感、舷窗冷光掠过侧脸",
    },
]

NPC_ARCHETYPES = [
    {
        "state": "试探",
        "preference": "能力与掌控",
        "psychology": "优先评估可利用价值与风险。",
    },
    {
        "state": "暧昧",
        "preference": "情绪价值与安全感",
        "psychology": "希望被理解，但不会轻易交出底牌。",
    },
    {
        "state": "戒备",
        "preference": "体面与秩序",
        "psychology": "重视边界，一旦失控会迅速抽离。",
    },
    {
        "state": "亲近",
        "preference": "共同利益与长期绑定",
        "psychology": "愿意靠近，但会持续测试你的兑现能力。",
    },
]

FEMALE_NAMES = [
    "顾晚晴",
    "林若曦",
    "沈知意",
    "许清禾",
    "宋以宁",
    "陆知薇",
    "程雨棠",
    "苏念安",
]


def create_initial_state() -> GameState:
    scene_tpl = random.choice(SCENE_TEMPLATES)
    name_pool = random.sample(FEMALE_NAMES, k=2)
    npc_pool = random.sample(NPC_ARCHETYPES, k=2)

    npc_list = []
    for i in range(2):
        npc_list.append(
            NPC(
                name=name_pool[i],
                favorability=random.randint(30, 50),
                state=npc_pool[i]["state"],
                preference=npc_pool[i]["preference"],
                psychology=npc_pool[i]["psychology"],
            )
        )

    return GameState(
        charm=3,
        wealth=5,
        reputation=2,
        npcs=npc_list,
        story_log=[],
        scene=scene_tpl["scene"],
        current_event=scene_tpl["event"],
        turn=0,
        choices=[
            Choice(id="A", text="高调展示资源，主导话题节奏", type="A"),
            Choice(id="B", text="切入情绪沟通，低声试探对方真实意图", type="B"),
            Choice(id="C", text="暂缓表态，观察两人的反应", type="C"),
        ],
    )
