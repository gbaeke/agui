"""Bedtime story sub-agent and tool."""

from agent_framework import Agent

from utils import create_chat_client

# Create a BedTimeStory agent that generates children's bedtime stories
bedtime_story_agent = Agent(
    name="BedTimeStoryTeller",
    description="A creative storyteller that writes engaging bedtime stories for children",
    instructions="""You are a gentle and creative bedtime story teller. 
When given a topic or theme, create a short, soothing bedtime story suitable for children.
Your stories should:
- Be 3-5 paragraphs long
- Have a calming, peaceful tone
- Include a gentle moral or lesson
- End on a peaceful note that encourages sleep
- Be age-appropriate and imaginative""",
    client=create_chat_client(),
)

# Convert the bedtime story agent to a tool
bedtime_story_tool = bedtime_story_agent.as_tool(
    name="tell_bedtime_story",
    description="Generate a calming bedtime story for children based on a given theme or topic",
    arg_name="theme",
    arg_description="The theme or topic for the bedtime story (e.g., 'a brave little rabbit', 'magical forest', 'friendly dragon')",
)
