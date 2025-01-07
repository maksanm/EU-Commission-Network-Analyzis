from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain_openai import ChatOpenAI


# TODO: rework, tavily works awful
class CabinetMemberMatchingChain:
    def __init__(self, comissioners):
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.0)
        self.retriever = TavilySearchAPIRetriever(
                k=1,
                include_generated_answer=True,
                #include_domains=["https://commissioners.ec.europa.eu/", "https://www.linkedin.com/in/"],
                #search_depth="advanced",
            )
        self.MEMBER_MATCH_PROMPT="""<RETRIEVED-DATA>
{retrieved_data}
</RETRIEVED-DATA>

Based on the retrieved information above, determine which of the following European Commissioners the {cabinet_member} belongs to.
Return only one of the records listed above, matching the retrieved data. If retrieved data does not specify the Commissioner, use your knowledge:

<COMMISSIONERS-LIST>
""" + "\n".join(comissioners) + """
</COMMISSIONERS-LIST>
"""

    def invoke(self, cabinet_member):
        chain = (
            RunnablePassthrough.assign(
                retrieved_data=self._retrieve_cabinet_member_data
            )
            | PromptTemplate.from_template(self.MEMBER_MATCH_PROMPT)
            | self.llm
            | StrOutputParser()
        )
        return chain.invoke({"cabinet_member": cabinet_member})

    def _retrieve_cabinet_member_data(self, cabinet_member):
        retriever_query = f"Who is the European Commissioner (2019-2024) leading the team {cabinet_member} belongs to."
        result = self.retriever.invoke(retriever_query)[0].page_content
        print(result)
        return self.retriever.invoke(retriever_query)[0].page_content
