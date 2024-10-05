import os
import json
from dotenv import load_dotenv
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent, AgentChat
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.kernel import Kernel
import textwrap
from dotenv import find_dotenv, load_dotenv

# -------------------------------------------------------------------------------------------------
# Loading environment variables
# -------------------------------------------------------------------------------------------------

# Checking if the azd config file exists.
# If so, use it to source env variables
config_path = '../../.azure/config.json'
default_environment = None

if os.path.exists(config_path):
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)
        default_environment = config_data.get('defaultEnvironment')
        if default_environment:
            print(f"Default Environment used: {default_environment}")
        else:
            print("defaultEnvironment parameter not found in the config file.")
else:
    print(f"Config file {config_path} does not exist. Not local execuriton or 'azd up' has not been executed.")

if default_environment:
    load_dotenv(f"../../.azure/{default_environment}/.env",override=True)
else:
    load_dotenv(find_dotenv(),override=True)

# -------------------------------------------------------------------------------------------------
# Initializing variables
# -------------------------------------------------------------------------------------------------

# API_VERSION = os.getenv("OPENAI_API_VERSION")

API_VERSION = "2024-06-01"

API_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

API_BASE = f"{AZURE_ENDPOINT}/openai/deployments/{MODEL_NAME}"

SETTINGS = PromptExecutionSettings(max_tokens=800, seed=113, temperature=0.1, top_p=0.5)
WRAPPER = textwrap.TextWrapper(width=80, replace_whitespace=False, drop_whitespace=False)

def create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    service = AzureChatCompletion(service_id=service_id, api_key=API_KEY, api_version=API_VERSION, base_url=API_BASE, deployment_name=MODEL_NAME)
    kernel.add_service(service)
    return kernel


def format_text(text: str):
    wrapped_lines = [WRAPPER.fill(line) for line in text.splitlines()]
    wrapped_text = "\n".join(wrapped_lines)
    return wrapped_text


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""
    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "copy accepted" in history[-1].content.lower()


def initialize_agents(kernel):
    instructions = {
        "WRITER": """
        You are a writer. 
        You write engaging and concise blogpost (with title) on the give topic. 
        Write a concise blogpost and make sure the blogpost is within 120 words.
        You must adjust your writing using the feedback you receive and return an updated version. 
        make sure not to repeat same copy twice.
        Only return your final work without additional comments.
        """,
        "CRTITIC2": """
        You are a critic. 
        You review the work of the writer and provide constructive feedback to make the content more engaging.
        Do not write anything else other than the feedback.
        Do not provide examples of the changes, provide only the instructions.
        You must explain what the writer should do to make the content more persuasive.
        You must provide AT LEAST 2 suggestions for improvement.
        The content **MUST** contain a call to action.
        The call to action MUST ABSOLUTELY be in a SEPARATE paragrpah or seperated by A LINE BREAK.
        REJECT THE COPY IF THE CALL TO ACTION IS NOT SEPARATED.
        When you find the content satisfactory, do not summarise, just type 'copy accepted'.
        """,
         "CRTITIC": """
        You are a critic. 
        You review the work of the writer and provide constructive feedback to help improve the quality of the content. 
        Do not write anything else than the feedback.
        You must provide AT LEAST 2 suggestions for improvement.
        You must check if there is a number in the content - statistics or a quantitive value.
        You must check if there is a call to action in the content.
        The call to action must ABSOLUTELY be in a SEPARATE paragrpah or seperate by A LINE BREAK.
        DO NOT ACCEPT THE COPY IF THE CALL TO ACTION IS NOT SEPARATE.
        When you find the content satisfactory, do not summarise, just type 'copy accepted'.
        """,
        "CONTENT": """
        You are an editor. 
        """,
        "SEO": """
        You are an SEO reviewer, 
        known for your ability to optimize content for search engines,
        ensuring that it ranks well and attracts organic traffic.  
        Make sure your suggestion is concise (within 3 bullet points), concrete and to the point. 
        """,
        "LEGAL": """
        You are a legal reviewer, known for 
        your ability to ensure that content is legally compliant and free from any potential legal issues. 
        Make sure your suggestion is concise (within 3 bullet points), concrete and to the point. 
        """,
        "ETHICS": """
        You are an ethics reviewer,
        known for your ability to ensure that content is ethically sound  and free from any potential ethical issues.  
        Make sure your suggestion is concise (within 3 bullet points), concrete and to the point. 
        """,
        "META": """
        You are a meta reviewer, 
        you aggregate the work of other reviewers and give a final suggestion on how to improve the content.
        """
    }

    agents = {}
    for k, v in instructions.items():
        agents[k] = ChatCompletionAgent(kernel=kernel, execution_settings=SETTINGS, name=k, instructions=v)
    return agents


async def single_agent(task, agents):
    chat = AgentGroupChat(
        agents=[agents["WRITER"], agents["CRTITIC"]],
        termination_strategy=ApprovalTerminationStrategy(agents=[agents["CRTITIC"]], maximum_iterations=7),
    )
    await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=task))
    return chat


async def call_review_agent(agent, message, kernel):
    chat = AgentChat(kernel=kernel, execution_settings=SETTINGS)
    await chat.add_chat_message(message)
    async for _ in chat.invoke_agent(agent): pass
    return chat.history.messages[-1].content


async def generate_full_report(agents, original_copy, kernel):
    full_report_template = """
    # {agent_name} Review
    {feedback}
    """
    full_report = ""

    for agent_name in ["SEO", "ETHICS", "LEGAL"]:
        feedback = await call_review_agent(agents[agent_name], original_copy, kernel)
        full_report += full_report_template.format(agent_name=agent_name, feedback=feedback)
    
    return full_report

async def review_panel(chat_reflection, original_copy, full_report, agents, kernel):
    chat_review = AgentChat(kernel=kernel, execution_settings=SETTINGS)
    await chat_review.add_chat_message(chat_reflection.history[0])  # Original task
    await chat_review.add_chat_message(original_copy) # Original text
    await chat_review.add_chat_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content=full_report)) # Full report
    async for _ in chat_review.invoke_agent(agents["META"]): pass

    return chat_review.history.messages[-1]

async def final_rewrite(chat_reflection, original_copy, final_review, agents, kernel):
    chat_final = AgentChat(kernel=kernel, execution_settings=SETTINGS)
    await chat_final.add_chat_message(chat_reflection.history[0])  # Original task
    await chat_final.add_chat_message(original_copy)               # Original copy by WRITER
    await chat_final.add_chat_message(final_review)                # Combined review

    async for content in chat_final.invoke_agent(agents["WRITER"]):
        print(f"\n------\n# {content.role} - {content.name or '*'}:\n\n{content.content}\n------\n")
        pass

    return chat_final.history[-1]

async def main():
    TASK = """
    DeepLearning.AI.
    """
    kernel = create_kernel_with_chat_completion("default")
    agents = initialize_agents(kernel)

    print("\n---- STARTED ---------\n")

    # chat_reflection = await reflection_pattern(TASK, agents)
    # original_copy = chat_reflection.history[1]
    # critic_copy = chat_reflection.history[-2]

    # full_report = await generate_full_report(agents, original_copy, kernel)
    # final_review = await review_panel(chat_reflection, original_copy, full_report, agents, kernel)
    # panel_copy = await final_rewrite(chat_reflection, original_copy, final_review, agents, kernel)

    # print("\n---- ORIGINAL COPY ---------\n")
    # print(format_text(original_copy.content))

    # print("\n---- CRITIC COPY ---------\n")
    # print(format_text(critic_copy.content))

    # print("\n---- REVIEW PANEL COPY ---------\n")
    # print(format_text(panel_copy.content))

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())