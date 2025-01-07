from dotenv import load_dotenv
load_dotenv()

import requests
import json
import glob
import faiss
from os import path
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_openai import OpenAIEmbeddings

from chains.commissioners_data_chain import CommissionersDataChain


class CommissionersDataScraper:
    def __init__(self):
        self.pdf_url = "https://www.cliffordchance.com/content/dam/cliffordchance/briefings/2020/10/the-european-commission-2019-2024.pdf"

        # Initialize FAISS index and embeddings
        index = faiss.IndexFlatL2()
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vectorstore = FAISS(
            embedding_function=self.embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )

        # Load unique attendees from a JSON file scrapped before
        with open(r"data\meetings\unique_attendees.json", encoding="utf-8") as file:
            self.unique_attendees = json.load(file)["unique_attendees"]
        self.comissioners = [att for att in self.unique_attendees if "Commissioner" in att or "President" in att]


    def _download_pdf(self, output_path):
        response = requests.get(self.pdf_url)
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                file.write(response.content)
            print(f"PDF downloaded successfully: {output_path}")
        else:
            raise Exception(f"Failed to download PDF. Status code: {response.status_code}")


    def _create_vectorstore(self, pdf_path, vectorstore_path):
        loader = PyPDFLoader(pdf_path)
        pages = []
        for page in loader.lazy_load():
            pages.append(page)
        pages = pages[6:33]
        self.vectorstore.add_texts([page.page_content for page in pages])
        self.vectorstore.save_local(vectorstore_path)


    def scrape(self, output_path="data/members"):
        # Download PDF if it doesn't exist locally
        pdf_path = path.join(output_path, "comissioners.pdf")
        if not path.exists(pdf_path):
            self._download_pdf(pdf_path)

        # Create new vectorstore or load an existing if available
        vectorstore_path = path.join(output_path, "commissioners_pdf_index")
        if not path.exists(vectorstore_path):
            self._create_vectorstore(pdf_path, vectorstore_path)
        else:
            self.vectorstore = FAISS.load_local(vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)

        # Instantiate a CommissionersDataChain with the vectorstore
        chain = CommissionersDataChain(self.vectorstore)
        # Retrieve data for each commissioner
        final_json = {"commissioners": []}
        for commissioner in self.comissioners:
            print(f"Retrieving data for {commissioner}")
            commissioner_json = {"name": commissioner} | chain.invoke(commissioner)
            print(f"Retrieved: \n{json.dumps(commissioner_json)}\n")
            final_json["commissioners"].append(commissioner_json)
        with open(path.join(output_path, "commisioners_data.json"), 'w', encoding='utf-8') as f:
            json.dump(final_json, f, ensure_ascii=False, indent=4)


# Example usage
if __name__ == "__main__":
    scraper = CommissionersDataScraper()
    scraper.scrape()
