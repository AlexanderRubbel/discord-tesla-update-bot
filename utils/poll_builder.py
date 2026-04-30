import datetime

import discord


def build_version_poll(version_id: str) -> discord.Poll:
    poll = discord.Poll(
        question=f"Have you installed version {version_id}?",
        duration=datetime.timedelta(days=7),
        multiple=False,
    )
    poll.add_answer(text="Yes, installed", emoji="\u2705")
    poll.add_answer(text="Not yet", emoji="\u23f3")
    poll.add_answer(text="No, skipping this one", emoji="\u274c")
    return poll
