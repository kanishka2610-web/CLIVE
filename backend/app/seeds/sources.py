from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.app.models.source import Source
from backend.app.models.story import Story
from backend.app.models.preference import TopicWeight
from backend.app.services.normalizer import canonicalize_url, normalize_title, generate_content_hash

DEFAULT_SOURCES = [
    {
        "name": "Anthropic Research & News",
        "url": "https://www.anthropic.com/news/feed.xml",
        "feed_type": "rss",
        "category": "Lab",
        "icon_url": "https://www.anthropic.com/favicon.ico"
    },
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "feed_type": "rss",
        "category": "Lab",
        "icon_url": "https://openai.com/favicon.ico"
    },
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "feed_type": "rss",
        "category": "Lab",
        "icon_url": "https://deepmind.google/favicon.ico"
    },
    {
        "name": "Meta AI Research",
        "url": "https://ai.meta.com/blog/rss.xml",
        "feed_type": "rss",
        "category": "Lab",
        "icon_url": "https://ai.meta.com/favicon.ico"
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "feed_type": "rss",
        "category": "Open Source",
        "icon_url": "https://huggingface.co/favicon.ico"
    },
    {
        "name": "Mistral AI News",
        "url": "https://mistral.ai/news/index.xml",
        "feed_type": "rss",
        "category": "Lab",
        "icon_url": "https://mistral.ai/favicon.ico"
    },
    {
        "name": "Simon Willison AI Weblog",
        "url": "https://simonwillison.net/atom/everything/",
        "feed_type": "atom",
        "category": "Industry",
        "icon_url": "https://simonwillison.net/static/favicon.ico"
    },
    {
        "name": "ArXiv CS.AI Artificial Intelligence",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "feed_type": "rss",
        "category": "Research",
        "icon_url": "https://arxiv.org/favicon.ico"
    },
    {
        "name": "Microsoft Research AI",
        "url": "https://www.microsoft.com/en-us/research/feed/",
        "feed_type": "rss",
        "category": "Research",
        "icon_url": "https://www.microsoft.com/favicon.ico"
    },
    {
        "name": "NVIDIA Technical Blog",
        "url": "https://developer.nvidia.com/blog/feed",
        "feed_type": "rss",
        "category": "Hardware",
        "icon_url": "https://developer.nvidia.com/favicon.ico"
    }
]

INITIAL_STORIES = [
    {
        "source_name": "Anthropic Research & News",
        "url": "https://www.anthropic.com/news/claude-3-7-sonnet-hybrid-reasoning",
        "title": "Claude 3.7 Sonnet and Extended Thinking: Hybrid Reasoning Architecture",
        "category": "LLMs",
        "sub_category": "Hybrid Reasoning",
        "companies": ["Anthropic"],
        "technologies": ["Claude 3.7", "Extended Thinking", "Hybrid Architecture"],
        "topics": ["Reasoning", "Coding Benchmarks", "Frontier LLM"],
        "importance_score": 96.0,
        "novelty_score": 92.0,
        "technical_score": 88.0,
        "is_breaking": True,
        "headline": "Anthropic Unveils Claude 3.7 Sonnet with Dynamic Extended Thinking",
        "summary": "Anthropic has released Claude 3.7 Sonnet, the industry's first hybrid reasoning model that seamlessly balances instantaneous answers with user-controlled step-by-step thinking tokens.",
        "why_it_matters": [
            "Introduces granular API control over thinking token budgets for complex reasoning tasks.",
            "Sets new state-of-the-art benchmarks in software engineering (SWE-bench Verified) and front-end coding.",
            "Eliminates the trade-off between latency-sensitive chat and deep deliberative problem solving."
        ],
        "hours_ago": 2
    },
    {
        "source_name": "OpenAI News",
        "url": "https://openai.com/index/introducing-deep-research",
        "title": "Introducing Deep Research: Autonomous Multi-Step Synthesis Agent",
        "category": "Agents",
        "sub_category": "Autonomous Research",
        "companies": ["OpenAI"],
        "technologies": ["o3", "Deep Research Agent", "Web Browsing"],
        "topics": ["Autonomous Agents", "Information Synthesis", "Enterprise Workflows"],
        "importance_score": 93.5,
        "novelty_score": 90.0,
        "technical_score": 85.0,
        "is_breaking": True,
        "headline": "OpenAI Launches Deep Research for Multi-Step Autonomous Synthesis",
        "summary": "OpenAI unveiled Deep Research, an autonomous agent that navigates dozens of technical documents, cross-references sources, and writes exhaustive reports in minutes.",
        "why_it_matters": [
            "Transforms analyst workflows from hours of manual collation to autonomous agentic synthesis.",
            "Demonstrates practical test-time compute scaling on complex search-and-verify loops.",
            "Accelerates competitive pressure on vertical AI intelligence products."
        ],
        "hours_ago": 5
    },
    {
        "source_name": "Google DeepMind Blog",
        "url": "https://deepmind.google/discover/blog/gemini-2-5-flash-thinking-mode",
        "title": "Gemini 2.5 Flash and Native Multimodal Reasoning at Scale",
        "category": "Multimodal",
        "sub_category": "Multimodal Reasoning",
        "companies": ["Google DeepMind", "Google"],
        "technologies": ["Gemini 2.5", "Flash Thinking", "Audio-Visual Native"],
        "topics": ["Multimodal AI", "Real-Time Inference", "TPUv5e"],
        "importance_score": 91.0,
        "novelty_score": 88.0,
        "technical_score": 86.0,
        "is_breaking": False,
        "headline": "Google DeepMind Releases Gemini 2.5 Flash with Real-Time Video-Audio Reasoning",
        "summary": "DeepMind's newest Flash variant integrates live video streaming understanding with native chain-of-thought token generation at sub-second latencies.",
        "why_it_matters": [
            "Brings frontier multimodal intelligence to cost-effective production deployment tiers.",
            "Enables embodied AI and robotics pipelines to process continuous video streams with low inference cost.",
            "Reinforces Google's full-stack advantage combining custom TPU infrastructure and efficient distillation."
        ],
        "hours_ago": 9
    },
    {
        "source_name": "Meta AI Research",
        "url": "https://ai.meta.com/blog/llama-4-scaffold-open-weights-breakthrough",
        "title": "Llama 4 Architectural Preview: Native Mixture-of-Experts and 1M Context",
        "category": "Open Source",
        "sub_category": "Open Weights",
        "companies": ["Meta"],
        "technologies": ["Llama 4", "MoE Architecture", "RoPE Scaling"],
        "topics": ["Open Source", "Mixture of Experts (MoE)", "Massive Context"],
        "importance_score": 94.0,
        "novelty_score": 91.0,
        "technical_score": 93.0,
        "is_breaking": True,
        "headline": "Meta Teases Llama 4 Architecture with 1M Context MoE Scaffold",
        "summary": "Meta AI has released architectural blueprints for the upcoming Llama 4 family, featuring sparse Mixture-of-Experts routing designed to run efficiently on commodity enterprise clusters.",
        "why_it_matters": [
            "Democratizes trillion-token context reasoning for on-premise enterprise deployments.",
            "Reduces inference compute per token by up to 60% compared to dense predecessors.",
            "Signals massive continued commitment to the open-weights AI ecosystem."
        ],
        "hours_ago": 14
    },
    {
        "source_name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/smolagents-v2-mcp-integration",
        "title": "Smolagents v2: Lightweight Code Agents with Native Model Context Protocol (MCP)",
        "category": "Tooling",
        "sub_category": "Developer Tooling",
        "companies": ["Hugging Face", "Anthropic"],
        "technologies": ["smolagents", "Model Context Protocol (MCP)", "Python Code Action"],
        "topics": ["Agent Workflows", "Tool Use", "Developer Ecosystem"],
        "importance_score": 84.0,
        "novelty_score": 82.0,
        "technical_score": 79.0,
        "is_breaking": False,
        "headline": "Hugging Face Integrates Model Context Protocol (MCP) into Smolagents v2",
        "summary": "Hugging Face's lightweight agent library now supports Anthropic's open MCP standard, allowing Python-written agents to connect to hundreds of standardized tool servers.",
        "why_it_matters": [
            "Solidifies Model Context Protocol as the prevailing industry standard for LLM tool integration.",
            "Code-based actions execute up to 3x faster than traditional JSON-RPC function calling loops.",
            "Simplifies local and self-hosted agent development."
        ],
        "hours_ago": 18
    },
    {
        "source_name": "Mistral AI News",
        "url": "https://mistral.ai/news/codestral-2501-code-generation-sota",
        "title": "Codestral 2501: State-of-the-Art Code Intelligence with 256k Context",
        "category": "LLMs",
        "sub_category": "Code Generation",
        "companies": ["Mistral AI"],
        "technologies": ["Codestral 2501", "Fill-in-the-Middle (FIM)", "Quantized Weights"],
        "topics": ["Code Generation", "Developer Tooling", "Low Latency"],
        "importance_score": 87.5,
        "novelty_score": 80.0,
        "technical_score": 84.0,
        "is_breaking": False,
        "headline": "Mistral AI Releases Codestral 2501 for Lightning-Fast IDE Autocompletion",
        "summary": "Codestral 2501 delivers specialized Fill-in-the-Middle code completion and whole-repo refactoring across 80+ programming languages with reduced memory overhead.",
        "why_it_matters": [
            "Provides an open-weights local coding companion capable of running on single consumer GPUs.",
            "Achieves superior accuracy on long-range repo context compared to larger general-purpose models.",
            "Offers flexible Apache 2.0 / research licensing tiers."
        ],
        "hours_ago": 26
    },
    {
        "source_name": "Microsoft Research AI",
        "url": "https://www.microsoft.com/en-us/research/blog/graphrag-v2-knowledge-agents",
        "title": "GraphRAG 2.0: Dynamic Knowledge Graph Construction with Reasoning Agents",
        "category": "Research",
        "sub_category": "RAG & Knowledge Graphs",
        "companies": ["Microsoft"],
        "technologies": ["GraphRAG", "Knowledge Graphs", "Hierarchical Summarization"],
        "topics": ["RAG", "Knowledge Representation", "Enterprise AI"],
        "importance_score": 86.0,
        "novelty_score": 84.0,
        "technical_score": 90.0,
        "is_breaking": False,
        "headline": "Microsoft GraphRAG 2.0 Unlocks Global Sensemaking Over Millions of Documents",
        "summary": "Microsoft Research published GraphRAG 2.0, upgrading graph extraction algorithms with entity resolution agents and modular hierarchical community detection.",
        "why_it_matters": [
            "Solves the 'needle in a haystack' synthesis limitation of naive vector RAG systems.",
            "Enables global thematic queries over entire enterprise datasets without losing micro-level facts.",
            "Reduces graph generation indexing costs by 45%."
        ],
        "hours_ago": 34
    },
    {
        "source_name": "Simon Willison AI Weblog",
        "url": "https://simonwillison.net/2026/feb/local-llms-inference-hardware-trends",
        "title": "The State of Local LLMs and Unified Memory Hardware Architectures",
        "category": "Hardware",
        "sub_category": "Inference Acceleration",
        "companies": ["Apple", "NVIDIA"],
        "technologies": ["Unified Memory", "vLLM", "Metal Performance Shaders"],
        "topics": ["Local Inference", "Hardware", "Developer Workstations"],
        "importance_score": 81.0,
        "novelty_score": 75.0,
        "technical_score": 82.0,
        "is_breaking": False,
        "headline": "Practical Analysis: Running 70B Quantized Models on Modern Unified Memory",
        "summary": "An in-depth breakdown of how unified memory architectures and kernel optimizations are making 70B parameter models practical for local developer workstations.",
        "why_it_matters": [
            "Exposes key memory bandwidth bottlenecks and quantization trade-offs for builders.",
            "Demystifies cost models between cloud API calls versus dedicated on-premise hardware.",
            "Provides reproducible benchmarks across Mac, Linux, and consumer GPUs."
        ],
        "hours_ago": 48
    },
    {
        "source_name": "ArXiv CS.AI Artificial Intelligence",
        "url": "https://arxiv.org/abs/2501.12948-deepseek-r1-incentivizing-reasoning",
        "title": "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning",
        "category": "Research",
        "sub_category": "Reinforcement Learning",
        "companies": ["DeepSeek"],
        "technologies": ["DeepSeek-R1", "GRPO", "Cold-Start Data"],
        "topics": ["Reasoning", "Reinforcement Learning", "Open Weights"],
        "importance_score": 98.0,
        "novelty_score": 96.0,
        "technical_score": 95.0,
        "is_breaking": True,
        "headline": "DeepSeek Publishes Landmark R1 Paper on Pure RL Reasoning Without Supervised Warmup",
        "summary": "DeepSeek revealed their Group Relative Policy Optimization (GRPO) training methodology, showing frontier reasoning models can emerge directly from reward modeling without millions of human annotations.",
        "why_it_matters": [
            "Challenges incumbent scaling paradigm by dramatically reducing data curation bottlenecks.",
            "Enables distillation of frontier reasoning capabilities into small 1.5B to 14B models.",
            "Sparks massive open-weights fine-tuning and replication efforts worldwide."
        ],
        "hours_ago": 52
    },
    {
        "source_name": "NVIDIA Technical Blog",
        "url": "https://developer.nvidia.com/blog/blackwell-b200-nvlink-5-inference-clusters",
        "title": "Scaling Ultra-Fast Inference on NVIDIA Blackwell B200 and NVLink 5 Clusters",
        "category": "Hardware",
        "sub_category": "GPU Infrastructure",
        "companies": ["NVIDIA"],
        "technologies": ["Blackwell B200", "NVLink 5", "TensorRT-LLM", "FP4 Precision"],
        "topics": ["GPU Infrastructure", "Inference Acceleration", "Hardware"],
        "importance_score": 89.0,
        "novelty_score": 85.0,
        "technical_score": 92.0,
        "is_breaking": False,
        "headline": "NVIDIA Blackwell B200 Delivers 30x Real-Time LLM Inference Throughput with FP4",
        "summary": "NVIDIA detailed architectural benchmarks for NVLink 5 domain switches and second-generation Transformer Engines running 4-bit floating point inference clusters.",
        "why_it_matters": [
            "Enables multi-trillion parameter MoE models to run within single NVLink domains without InfiniBand latency hops.",
            "Drops datacenter power consumption per million tokens by up to 25x.",
            "Sets the hardware standard for upcoming frontier models through 2026."
        ],
        "hours_ago": 60
    }
]

def seed_database_if_empty(db: Session):
    """Populates database with curated default sources and high-signal stories if empty."""
    # 1. Seed Sources
    source_map = {}
    for src_data in DEFAULT_SOURCES:
        existing = db.query(Source).filter(Source.url == src_data["url"]).first()
        if not existing:
            src = Source(
                name=src_data["name"],
                url=src_data["url"],
                feed_type=src_data["feed_type"],
                category=src_data["category"],
                icon_url=src_data.get("icon_url"),
                is_active=True,
                last_scanned_at=datetime.now(timezone.utc),
                last_success_at=datetime.now(timezone.utc)
            )
            db.add(src)
            db.commit()
            db.refresh(src)
            source_map[src.name] = src
        else:
            source_map[existing.name] = existing

    # 2. Seed Initial Stories
    now = datetime.now(timezone.utc)
    for st in INITIAL_STORIES:
        canonical = canonicalize_url(st["url"])
        existing_story = db.query(Story).filter(Story.canonical_url == canonical).first()
        if not existing_story:
            src = source_map.get(st["source_name"])
            if not src:
                src = db.query(Source).first()
                
            norm_title = normalize_title(st["title"])
            hash_sig = generate_content_hash(canonical, norm_title, st["summary"])
            pub_time = now - timedelta(hours=st.get("hours_ago", 1))

            story = Story(
                source_id=src.id,
                canonical_url=canonical,
                original_url=st["url"],
                title=st["title"],
                normalized_title=norm_title,
                hash_signature=hash_sig,
                author=src.name,
                raw_content=st["summary"],
                extracted_content=st["summary"],
                published_at=pub_time,
                is_ai_related=True,
                category=st["category"],
                sub_category=st.get("sub_category"),
                companies=st.get("companies", []),
                technologies=st.get("technologies", []),
                topics=st.get("topics", []),
                importance_score=st["importance_score"],
                novelty_score=st["novelty_score"],
                technical_score=st["technical_score"],
                is_breaking=st.get("is_breaking", False),
                headline=st["headline"],
                summary=st["summary"],
                why_it_matters=st.get("why_it_matters", []),
                status="processed"
            )
            db.add(story)
    db.commit()

    # 3. Seed Default Topic Weights for baseline personalization
    default_topics = [
        ("LLMs", 1.2),
        ("Agents", 1.25),
        ("Multimodal", 1.1),
        ("Reasoning", 1.3),
        ("Open Source", 1.15),
        ("Hardware", 1.05),
        ("OpenAI", 1.1),
        ("Anthropic", 1.2),
        ("Google DeepMind", 1.1),
        ("Meta", 1.1),
        ("DeepSeek", 1.3)
    ]
    for topic, weight in default_topics:
        existing_w = db.query(TopicWeight).filter(
            TopicWeight.user_id == "default_user",
            TopicWeight.topic == topic
        ).first()
        if not existing_w:
            tw = TopicWeight(
                user_id="default_user",
                topic=topic,
                weight=weight,
                positive_count=1,
                negative_count=0
            )
            db.add(tw)
    db.commit()
