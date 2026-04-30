import datetime

import discord


def build_version_poll(version_id: str) -> discord.Poll:
    poll = discord.Poll(
        question=f"Does FSD {version_id} work on your hardware?",
        duration=datetime.timedelta(days=7),
        multiple=False,
    )
    poll.add_answer(text="HW3 working", emoji="\U0001f7e2")
    poll.add_answer(text="HW4 working", emoji="\U0001f7e2")
    poll.add_answer(text="Both working", emoji="\u2705")
    poll.add_answer(text="HW3 not working", emoji="\U0001f534")
    poll.add_answer(text="HW4 not working", emoji="\U0001f534")
    return poll
