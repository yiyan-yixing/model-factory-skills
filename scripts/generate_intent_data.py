#!/usr/bin/env python3
"""
Generate intent classification + query rewrite dataset.
Simple, no infinite loops. Direct data writing.
"""

import json
import os
import random

random.seed(42)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "data", "intent")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Intent samples: (query, sub_intent, rewritten_query)
SAMPLES = {
    "chat": [
        ("你好", "greeting", "你好，我想和你打个招呼"),
        ("嗨", "greeting", "你好，我想和你打个招呼"),
        ("早上好", "greeting", "早上好，我想和你打个招呼"),
        ("你好呀", "greeting", "你好，我想和你打个招呼"),
        ("hello", "greeting", "你好，我想和你打个招呼"),
        ("嘿，在吗", "greeting", "你好，我想确认你是否在线"),
        ("晚上好", "greeting", "晚上好，我想和你打个招呼"),
        ("哈喽", "greeting", "你好，我想和你打个招呼"),
        ("早安", "greeting", "早上好，我想和你打个招呼"),
        ("hi，忙不忙", "greeting", "你好，我想确认你现在是否方便交流"),
        ("今天天气怎么样", "small_talk", "我想聊聊天，今天天气怎么样"),
        ("你是谁", "small_talk", "我想了解一下你是什么AI助手"),
        ("你会做什么", "small_talk", "我想了解你的能力和功能范围"),
        ("聊聊天吧", "small_talk", "我想和你闲聊一些话题"),
        ("说说你的看法", "small_talk", "我想听听你对某个话题的看法和观点"),
        ("无聊，陪我说说话", "small_talk", "我现在比较无聊，想和你聊聊天打发时间"),
        ("你有什么爱好", "small_talk", "我想闲聊，了解你的兴趣爱好"),
        ("推荐个电影", "small_talk", "我想闲聊，希望你推荐一部好看的电影"),
        ("你觉得自己有意识吗", "small_talk", "我想闲聊，讨论AI是否有自我意识这个哲学问题"),
        ("最近有什么好看的剧", "small_talk", "我想闲聊，希望你推荐最近热门的电视剧"),
        ("我今天心情不好", "emotion", "我心情低落，想找人倾诉和聊天"),
        ("我好开心啊", "emotion", "我心情很好，想分享我的喜悦"),
        ("最近压力好大", "emotion", "我感到压力很大，需要安慰和建议"),
        ("我好焦虑", "emotion", "我感到焦虑不安，想聊聊缓解情绪的方法"),
        ("我好孤独", "emotion", "我感到孤独，想找人说说话"),
        ("气死我了", "emotion", "我非常生气，想倾诉发泄情绪"),
        ("我好难过", "emotion", "我感到悲伤难过，需要安慰和陪伴"),
        ("有点沮丧", "emotion", "我感到沮丧，想聊聊调整心态的方法"),
        ("开心到飞起", "emotion", "我非常开心，想和人分享快乐"),
        ("心情复杂", "emotion", "我情绪复杂纠结，想梳理和倾诉内心感受"),
        ("你叫什么名字", "persona", "我想了解你的名称和身份信息"),
        ("你是GPT吗", "persona", "我想确认你是什么类型的AI模型"),
        ("你是什么模型", "persona", "我想了解你底层使用的AI模型架构"),
        ("你跟ChatGPT有什么区别", "persona", "我想比较你和其他AI助手的差异和特点"),
        ("你用的是哪个版本", "persona", "我想了解你当前的模型版本信息"),
    ],
    "search": [
        ("什么是量子计算", "factual", "请解释量子计算的基本概念和原理"),
        ("中国的首都是哪里", "factual", "请告诉我中国的首都城市名称"),
        ("太阳系有多少颗行星", "factual", "请列举太阳系中所有行星的数量"),
        ("Python是谁发明的", "factual", "请告诉我Python编程语言的创始人是谁"),
        ("光速是多少", "factual", "请告诉我光在真空中的传播速度数值"),
        ("地球到月球多远", "factual", "请告诉我地球到月球的平均距离"),
        ("DNA的全称是什么", "factual", "请告诉我DNA这个缩写的完整英文名称"),
        ("珠穆朗玛峰多高", "factual", "请告诉我珠穆朗玛峰的海拔高度"),
        ("水的化学式", "factual", "请告诉我水的化学分子式"),
        ("二战什么时候结束的", "factual", "请告诉我第二次世界大战结束的具体年份"),
        ("北京今天多少度", "factual", "请查询北京市今天的实时气温数据"),
        ("最新的iPhone是什么型号", "factual", "请查询苹果公司最新发布的iPhone手机型号"),
        ("宇宙有多大", "factual", "请解释可观测宇宙的大小和范围"),
        ("人类有多少块骨头", "factual", "请告诉成年人人体骨骼的数量"),
        ("怎么做红烧肉", "how_to", "请提供红烧肉的详细烹饪步骤和食材清单"),
        ("怎么学英语", "how_to", "请提供系统性的英语学习方法和学习路线建议"),
        ("如何减肥", "how_to", "请提供科学有效的减肥方法和饮食运动建议"),
        ("怎么安装Python", "how_to", "请提供Python编程环境的安装步骤和配置方法"),
        ("如何提高记忆力", "how_to", "请提供提高记忆力的科学方法和训练技巧"),
        ("怎么写简历", "how_to", "请提供专业简历的撰写方法和模板建议"),
        ("如何做PPT", "how_to", "请提供制作专业PPT演示文稿的步骤和技巧"),
        ("怎么烤蛋糕", "how_to", "请提供烤蛋糕的详细食谱和烘焙步骤"),
        ("如何学好数学", "how_to", "请提供系统性的数学学习方法和思维训练建议"),
        ("怎么冥想", "how_to", "请提供冥想入门的步骤和注意事项"),
        ("Python和Java哪个好", "comparison", "请对比Python和Java编程语言的优缺点和适用场景"),
        ("iPhone和安卓哪个好", "comparison", "请对比iPhone和安卓手机的优缺点和选择建议"),
        ("买房还是租房", "comparison", "请分析买房和租房的经济成本和利弊对比"),
        ("React和Vue哪个好", "comparison", "请对比React和Vue前端框架的特点和适用场景"),
        ("考研还是工作", "comparison", "请分析考研和直接工作的利弊和选择建议"),
        ("特斯拉和比亚迪怎么选", "comparison", "请对比特斯拉和比亚迪新能源汽车的性能和性价比"),
        ("你觉得AI会取代人类吗", "opinion", "请分析人工智能是否会取代人类工作的观点和论据"),
        ("未来什么行业最有前景", "opinion", "请分析未来十年最有发展前景的行业和原因"),
        ("如何看待内卷", "opinion", "请分析社会内卷现象的原因和应对建议"),
        ("远程办公好不好", "opinion", "请分析远程办公的利弊和适用条件"),
        ("应不应该读博", "opinion", "请分析攻读博士学位的利弊和适合人群"),
    ],
    "generation": [
        ("画一只猫", "image_gen", "请生成一张猫的图片，可爱风格，高清画质"),
        ("生成一张风景图", "image_gen", "请生成一张自然风景图片，包含山水，高清分辨率"),
        ("帮我做张海报", "image_gen", "请为我设计一张活动海报图片，现代简约风格，包含标题区域"),
        ("画个动漫女孩", "image_gen", "请生成一张动漫风格的少女插画，日系画风，彩色高清"),
        ("生成logo", "image_gen", "请为一个科技公司设计logo图片，简洁现代风格"),
        ("画一幅水墨画", "image_gen", "请生成一幅中国传统水墨画风格的山水画图片"),
        ("做个表情包", "image_gen", "请生成一套搞笑表情包图片，可爱卡通风格"),
        ("生成一张赛博朋克城市", "image_gen", "请生成一张赛博朋克风格的未来城市夜景图片，霓虹灯光，高清"),
        ("画个好看的", "image_gen", "请生成一张美观的风景图片，高清画质，色彩丰富"),
        ("帮我P一下这张图", "image_gen", "请对这张图片进行编辑处理，优化画质和色彩"),
        ("生成头像", "image_gen", "请生成一张个人头像图片，简约风格，适合社交媒体"),
        ("做个短视频", "video_gen", "请帮我制作一段15秒的短视频，内容为城市延时摄影"),
        ("生成动画", "video_gen", "请生成一段动画视频，卡通风格，30秒时长"),
        ("剪辑一下视频", "video_gen", "请帮我剪辑视频，裁剪精华片段并添加转场效果"),
        ("做个Vlog片头", "video_gen", "请制作一段Vlog视频片头动画，时尚简约风格，5秒"),
        ("生成一个转场效果", "video_gen", "请生成视频转场动画效果，渐变过渡风格"),
        ("做个产品宣传视频", "video_gen", "请制作一段产品宣传视频，展示产品特色，30秒时长"),
        ("配个BGM", "video_gen", "请为这段视频配上适合的背景音乐"),
        ("生成一段背景音乐", "audio_gen", "请生成一段轻柔的背景音乐，钢琴为主，3分钟时长"),
        ("做个音效", "audio_gen", "请生成一个按钮点击的音效，清脆短促"),
        ("帮我配音", "audio_gen", "请为这段文字生成女声配音，标准普通话，中等语速"),
        ("生成一首歌", "audio_gen", "请创作一首流行风格的歌曲，包含旋律和人声，3分钟"),
        ("帮我写首诗", "text_gen", "请创作一首关于春天的现代诗，4-8行，意境优美"),
        ("写个故事", "text_gen", "请创作一个短篇科幻故事，500字左右，情节紧凑"),
        ("帮我写个文案", "text_gen", "请为这款产品撰写营销推广文案，突出核心卖点"),
        ("生成一封邮件", "text_gen", "请撰写一封商务邀请邮件，语气正式，包含会议时间和议程"),
        ("写个剧本", "text_gen", "请创作一个5分钟短剧剧本，都市题材，包含对话和场景描写"),
        ("帮我写歌词", "text_gen", "请创作一首关于友情的流行歌曲歌词，包含主歌副歌"),
        ("写个段子", "text_gen", "请创作一个幽默搞笑的段子，适合社交媒体分享"),
        ("帮我写个演讲稿", "text_gen", "请撰写一篇5分钟的演讲稿，主题为创新，逻辑清晰有感染力"),
    ],
    "code": [
        ("写个快排", "write", "请用Python实现快速排序算法，包含完整代码和注释"),
        ("写个爬虫", "write", "请用Python编写一个网页爬虫程序，支持多线程和反爬处理"),
        ("实现一个LRU缓存", "write", "请用Python实现LRU缓存数据结构，支持get和put操作"),
        ("写个API接口", "write", "请用Flask框架编写RESTful API接口，包含增删改查功能"),
        ("写个二叉树遍历", "write", "请用Python实现二叉树的前序、中序和后序遍历算法"),
        ("写个排序算法", "write", "请实现常见排序算法，包括冒泡、选择、插入排序"),
        ("写个web服务器", "write", "请用Python实现一个简单的HTTP服务器，支持静态文件服务"),
        ("写个计算器", "write", "请实现一个支持四则运算和括号的计算器程序"),
        ("写个todolist", "write", "请用React编写一个待办事项应用，支持增删改和状态切换"),
        ("实现JWT认证", "write", "请用Node.js实现JWT用户认证，包含登录、注册和token验证"),
        ("写个链表反转", "write", "请用Python实现单链表反转算法，包含迭代和递归两种方法"),
        ("写个正则匹配", "write", "请编写正则表达式匹配并提取文本中的特定模式"),
        ("这段代码有bug", "debug", "请帮我排查代码中的bug，分析错误原因并提供修复方案"),
        ("为什么报错了", "debug", "请分析这段代码的报错原因，提供具体的修复方法"),
        ("我的代码跑不通", "debug", "请帮我调试代码，找出运行失败的原因并修复"),
        ("这个函数返回值不对", "debug", "请检查这个函数的逻辑错误，修复返回值不正确的问题"),
        ("内存泄漏了", "debug", "请帮我排查代码中的内存泄漏问题，定位泄漏点并提供修复方案"),
        ("死循环了", "debug", "请检查代码中的无限循环问题，分析原因并提供修复方案"),
        ("空指针异常", "debug", "请排查代码中的空指针异常，定位原因并提供修复方案"),
        ("索引越界了", "debug", "请检查数组索引越界的错误原因，提供修复方案"),
        ("解释一下这段代码", "explain", "请详细解释这段代码的逻辑和功能，逐行分析关键部分"),
        ("什么是闭包", "explain", "请详细解释编程中闭包的概念、原理和使用场景"),
        ("Docker怎么用", "explain", "请详细解释Docker容器技术的核心概念和基本使用方法"),
        ("解释一下React Hooks", "explain", "请详细解释React Hooks的工作原理和常用Hook的使用方法"),
        ("什么是微服务", "explain", "请详细解释微服务架构的概念、特点和与单体架构的区别"),
        ("解释一下Promise", "explain", "请详细解释JavaScript中Promise的概念、状态和使用方法"),
        ("优化这段代码", "refactor", "请重构这段代码，提升可读性、性能和可维护性"),
        ("代码太乱了帮我整理", "refactor", "请重构代码，改善命名规范、添加注释、优化代码结构"),
        ("性能太差了", "refactor", "请优化代码性能，识别性能瓶颈并提供优化方案"),
        ("帮我改成async", "refactor", "请将同步代码重构为异步实现，提升并发处理能力"),
        ("这段代码能精简吗", "refactor", "请精简重构代码，消除冗余逻辑，使用更简洁的写法"),
        ("太重复了，抽个函数", "refactor", "请提取重复代码为公共函数，减少冗余，提高复用性"),
    ],
    "math": [
        ("1+1等于几", "computation", "请计算1加1的结果"),
        ("123乘以456等于多少", "computation", "请计算123乘以456的结果"),
        ("2的10次方是多少", "computation", "请计算2的10次方的数值结果"),
        ("算一下15的阶乘", "computation", "请计算15的阶乘数值结果"),
        ("根号2约等于多少", "computation", "请计算根号2的近似值，保留到小数点后6位"),
        ("圆周率前10位", "computation", "请提供圆周率π的前10位小数"),
        ("100以内的质数有哪些", "computation", "请列出100以内所有质数的完整列表"),
        ("3的7次方", "computation", "请计算3的7次方的数值结果"),
        ("17乘以23", "computation", "请计算17乘以23的结果"),
        ("2的20次方等于多少", "computation", "请计算2的20次方的数值结果"),
        ("解方程x²-5x+6=0", "equation", "请求解一元二次方程x²-5x+6=0的所有根"),
        ("算积分∫x²dx", "equation", "请计算不定积分∫x²dx的结果"),
        ("求导数f(x)=x³+2x", "equation", "请对函数f(x)=x³+2x求导数"),
        ("解方程组x+y=5, x-y=1", "equation", "请求解二元一次方程组x+y=5, x-y=1的解"),
        ("求极限lim(x→0)sinx/x", "equation", "请计算极限lim(x→0)sinx/x的值"),
        ("解3x+7=22", "equation", "请求解一元一次方程3x+7=22中x的值"),
        ("求dy/dx 当y=x⁴-3x²+1", "equation", "请对函数y=x⁴-3x²+1求导数"),
        ("解2x²+3x-5=0", "equation", "请求解一元二次方程2x²+3x-5=0的所有根"),
        ("证明根号2是无理数", "proof", "请用反证法证明根号2是无理数，给出完整证明过程"),
        ("证明勾股定理", "proof", "请给出勾股定理a²+b²=c²的证明过程"),
        ("证明素数有无穷多个", "proof", "请用反证法证明素数有无穷多个"),
        ("证明1+2+...+n=n(n+1)/2", "proof", "请用数学归纳法证明1到n的求和公式"),
        ("算一下平均数", "statistics", "请计算这组数据的算术平均数"),
        ("求标准差", "statistics", "请计算这组数据的标准差，展示计算过程"),
        ("概率题：抛硬币3次全是正面的概率", "statistics", "请计算连续抛3次硬币都出现正面的概率"),
        ("算一下中位数", "statistics", "请计算这组数据的中位数"),
        ("求方差", "statistics", "请计算这组数据的方差，展示计算过程"),
        ("这个分布是正态的吗", "statistics", "请分析这组数据是否符合正态分布，提供检验方法"),
    ],
    "tool": [
        ("设个闹钟明天7点", "calendar", "请设置明天早上7:00的闹钟提醒"),
        ("提醒我下午3点开会", "calendar", "请设置今天下午3:00的会议提醒"),
        ("下周三有什么安排", "calendar", "请查询下周三的日程安排和待办事项"),
        ("帮我约个会议", "calendar", "请帮我创建一个新的会议日程，需要指定时间和参与者"),
        ("今天几号", "calendar", "请告诉我今天的日期和星期"),
        ("明天有什么安排", "calendar", "请查询明天的日程安排和待办事项"),
        ("发封邮件给张三", "email", "请帮我撰写并发送邮件给张三，需要确认邮件主题和内容"),
        ("帮我回一下这封邮件", "email", "请帮我回复这封邮件，需要确认回复内容"),
        ("检查未读邮件", "email", "请查询邮箱中所有未读邮件列表"),
        ("写封请假邮件", "email", "请帮我撰写一封请假邮件，语气正式，包含请假原因和时长"),
        ("翻译一下这段话", "translate", "请将这段文字翻译成英文，保持原文语义和语气"),
        ("这个英文什么意思", "translate", "请将这段英文翻译成中文，准确传达原文含义"),
        ("帮我翻成日语", "translate", "请将这段中文翻译成日语，使用标准敬语表达"),
        ("中翻英", "translate", "请将这段中文内容翻译成英文"),
        ("英翻中", "translate", "请将这段英文内容翻译成中文"),
        ("帮我整理一下文件", "file_op", "请帮我整理指定目录下的文件，按类型分类归档"),
        ("重命名这个文件", "file_op", "请将指定文件重命名为新名称"),
        ("压缩这些文件", "file_op", "请将选定的文件和文件夹压缩为ZIP格式"),
        ("找一下那个文档", "file_op", "请在指定目录中搜索包含关键字的文档文件"),
        ("删掉这些临时文件", "file_op", "请删除指定目录下的临时文件和缓存"),
        ("打开WiFi", "system", "请开启设备的WiFi无线网络连接"),
        ("调大音量", "system", "请将设备音量调大到80%"),
        ("截个屏", "system", "请对当前屏幕进行截图操作"),
        ("打开设置", "system", "请打开系统设置应用"),
        ("清理一下缓存", "system", "请清理应用的缓存数据，释放存储空间"),
    ],
}

# Prefix/suffix augmentation
PREFIXES = ["帮我", "能不能", "我想", "麻烦", "请问", "能不能帮我"]
SUFFIXES = ["吧", "呢", "啊", "一下", "可以吗", "嘛"]


def augment_query(query):
    """Generate variant queries."""
    variants = set()
    variants.add(query)
    if len(query) <= 12:
        for p in random.sample(PREFIXES, min(2, len(PREFIXES))):
            v = p + query
            if len(v) < 25:
                variants.add(v)
        for s in random.sample(SUFFIXES, min(2, len(SUFFIXES))):
            v = query + s
            if len(v) < 25:
                variants.add(v)
    return variants


def build_dataset():
    all_train = []
    all_eval = []
    all_test = []

    for intent, samples in SAMPLES.items():
        # Augment each sample
        augmented = []
        seen = set()
        for query, sub_intent, rewritten in samples:
            for variant in augment_query(query):
                if variant not in seen:
                    augmented.append((variant, sub_intent, rewritten))
                    seen.add(variant)

        # If still not enough, duplicate with more prefixes
        base_samples = list(samples)
        idx = 0
        while len(augmented) < 200 and idx < len(base_samples) * 5:
            query, sub_intent, rewritten = base_samples[idx % len(base_samples)]
            p = PREFIXES[idx % len(PREFIXES)]
            s = SUFFIXES[idx % len(SUFFIXES)]
            variant = p + query + s
            if variant not in seen and len(variant) < 30:
                augmented.append((variant, sub_intent, rewritten))
                seen.add(variant)
            idx += 1

        random.shuffle(augmented)

        # Split
        target = min(len(augmented), 200 if intent != "tool" else 100)
        data = augmented[:target]
        eval_size = int(target * 0.15)
        test_size = int(target * 0.15)
        train_size = target - eval_size - test_size

        for query, sub_intent, rewritten in data[:train_size]:
            all_train.append({
                "instruction": "分析用户输入的意图，输出意图分类和改写后的查询。",
                "input": query,
                "output": json.dumps({"intent": intent, "sub_intent": sub_intent, "rewritten_query": rewritten}, ensure_ascii=False)
            })

        for query, sub_intent, rewritten in data[train_size:train_size + eval_size]:
            all_eval.append({
                "instruction": "分析用户输入的意图，输出意图分类和改写后的查询。",
                "input": query,
                "output": json.dumps({"intent": intent, "sub_intent": sub_intent, "rewritten_query": rewritten}, ensure_ascii=False)
            })

        for query, sub_intent, rewritten in data[train_size + eval_size:train_size + eval_size + test_size]:
            all_test.append({
                "instruction": "分析用户输入的意图，输出意图分类和改写后的查询。",
                "input": query,
                "output": json.dumps({"intent": intent, "sub_intent": sub_intent, "rewritten_query": rewritten}, ensure_ascii=False)
            })

        print(f"  {intent}: {train_size} train, {eval_size} eval, {test_size} test (augmented: {len(augmented)})")

    random.shuffle(all_train)
    random.shuffle(all_eval)
    random.shuffle(all_test)

    # Save
    for name, data in [("train", all_train), ("eval", all_eval), ("test", all_test)]:
        path = os.path.join(OUTPUT_DIR, f"{name}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {name}.json: {len(data)} samples")

    # Stats
    print("\n--- Dataset Stats ---")
    for split_name, split_data in [("train", all_train), ("eval", all_eval), ("test", all_test)]:
        counts = {}
        for item in split_data:
            out = json.loads(item["output"])
            counts[out["intent"]] = counts.get(out["intent"], 0) + 1
        print(f"{split_name} ({len(split_data)}): {dict(sorted(counts.items()))}")

    # Schema
    schema = {
        "version": "1.0",
        "coarse_intents": list(SAMPLES.keys()),
        "sub_intents": {k: sorted(set(s[1] for s in v)) for k, v in SAMPLES.items()},
        "output_format": {
            "intent": "coarse intent (string)",
            "sub_intent": "fine-grained intent (string)",
            "rewritten_query": "expanded and clarified query (string)"
        }
    }
    with open(os.path.join(OUTPUT_DIR, "schema.json"), 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print("Saved schema.json")


if __name__ == "__main__":
    build_dataset()
