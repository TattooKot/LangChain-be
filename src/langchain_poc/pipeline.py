from .prompts import capital_prompt
from langchain_openai import ChatOpenAI

# Ініціалізація LLM
llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.0)
# Композиція pipe: prompt → llm
pipeline = capital_prompt | llm