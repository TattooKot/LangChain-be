from langchain.prompts import PromptTemplate

capital_prompt = PromptTemplate(
    input_variables=["country"],
    template="What is the capital of {country}?"
)