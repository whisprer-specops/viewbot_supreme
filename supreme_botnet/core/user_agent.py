# core/user_agent.py

import random

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "Mozilla/5.0 (X11; Linux x86_64)...",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X)...",
    # Add more high-quality ones later
]

class UserAgentManager:
    def __init__(self, agent_list=None):
        self.user_agents = agent_list or DEFAULT_USER_AGENTS

    def get_random_user_agent(self):
        return random.choice(self.user_agents)
