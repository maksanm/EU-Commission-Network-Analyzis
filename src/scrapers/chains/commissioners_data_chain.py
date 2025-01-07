from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough


class CommissionersDataChain:
    COMMISSIONER_DATA_PROMPT = """<RETRIEVED-DATA>
{retrieved_data}
</RETRIEVED-DATA>

Based on the retrieved information above, determine the age, education, and political group data for the commissioner named {commissioner}.

Select one or more education fields from the list below:
<EDUCATION-FIELDS>
- Law
- Economics
- Political Science
- International Relations
- Public Health and Medicine
- Engineering
- Humanities and Languages
- Social Sciences
- Environmental Studies
- Security and Defence Studies
- Education and Pedagogy
- Mathematics
- Psychology
</EDUCATION-FIELDS>

Return the data in the following JSON format:
{{
    "age": 45,
    "education": ["Engineering", "Economics"],
    "political_group": "EPP"
}}
If the retrieved data does not provide any relevant information about the specified commissioner, return empty JSON.
"""

    def __init__(self, vectorstore):
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.0)
        self.retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 1})


    def invoke(self, commissioner):
        chain = (
            RunnablePassthrough.assign(
                retrieved_data=self._retrieve_commissioner_data
            )
            | PromptTemplate.from_template(self.COMMISSIONER_DATA_PROMPT)
            | self.llm
            | JsonOutputParser()
        )
        return chain.invoke({"commissioner": commissioner})

    def _retrieve_commissioner_data(self, state):
        return self.retriever.invoke(state["commissioner"])[0].page_content
