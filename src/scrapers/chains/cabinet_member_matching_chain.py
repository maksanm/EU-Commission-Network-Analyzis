from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import Driver
from bs4 import BeautifulSoup
import os
import time



# TODO: rework, tavily works awful
class CabinetMemberMatchingChain:

    def __init__(self, commissioners):
        # Configure Selenium WebDriver using Chrome in GUI mode with Undetected ChromeDriver enabled
        self.options = Options()
        self.perplexity_driver = Driver(uc=True, headless=False)

        # Open URL using UC mode with 3 second reconnect time to bypass initial detection
        self.perplexity_driver.uc_open_with_reconnect(os.getenv("PERPLEXITY_URL"), reconnect_time=3)

        # Log into Perplexity manually
        input("Press Enter after you have manually logged into Perplexity...")

        self.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.0)
        self.COMMISSIONER_RECORD_MATCH_PROMPT="""<RETRIEVED-DATA>
{retrieved_data}
</RETRIEVED-DATA>

Based on the retrieved information above, identify and return the record of the European Commissioner whose cabinet includes the member {cabinet_member} from the list below. If the retrieved data does not containt the Commissioner from the list, return UNKNOWN.

<COMMISSIONERS-LIST>
""" + "\n".join(commissioners) + """
</COMMISSIONERS-LIST>

<RESPONSE_FORMAT>
{{
    "commissioner": "Name Surname (Commissioner)"
}}
</RESPONSE_FORMAT>
<UNKNOWN_FORMAT>
{{
    "commissioner": "UNKNOWN"
}}
</UNKNOWN_FORMAT>
"""


    def invoke(self, cabinet_member):
        chain = (
            RunnablePassthrough.assign(
                retrieved_data=self._retrieve_from_perplexity
            )
            | PromptTemplate.from_template(self.COMMISSIONER_RECORD_MATCH_PROMPT)
            | self.llm
            | JsonOutputParser()
        )
        return chain.invoke({"cabinet_member": cabinet_member})


    def _retrieve_from_perplexity(self, state):
        # Open URL using UC mode with 3 second reconnect time to bypass initial detection
        self.perplexity_driver.uc_open_with_reconnect(os.getenv("PERPLEXITY_URL"), reconnect_time=3)
        soup = BeautifulSoup(self.perplexity_driver.page_source, 'html.parser')
        # Find the textarea element using BeautifulSoup
        textarea = soup.find('textarea')
        # If the textarea is found, use Selenium to interact with it
        if textarea:
            # Find the textarea element using Selenium
            input_box = self.perplexity_driver.find_element(By.TAG_NAME, 'textarea')
            # Enter the prompt
            perplexity_prompt = f"If you know, specify which Commissioner's Cabinet {state['cabinet_member']} serves to during the 2019-2024 EU Commission. Return Cabinet and Commissioner full name"
            input_box.send_keys(perplexity_prompt)
            # Submit the prompt by pressing Enter
            input_box.send_keys(Keys.RETURN)
        # Wait for the response to be fully loaded
        time.sleep(1)
        wait = WebDriverWait(self.perplexity_driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.prose span")))
        time.sleep(3)
        # Get the updated page source
        page_source = self.perplexity_driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        # Find the div containing the response
        response_div = soup.find('div', class_='prose')
        # Extract the text from all spans within the div
        response_text = ''.join(span.get_text() for span in response_div.find_all('span'))
        # Return the response text
        return response_text
