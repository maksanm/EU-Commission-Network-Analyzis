from dotenv import load_dotenv
load_dotenv()

import json

from chains.cabinet_member_matching_chain import CabinetMemberMatchingChain


# TODO: rework, tavily works awful
class CabinetMembersMatchScraper:
    def __init__(self):
        with open(r"data\meetings\unique_attendees.json", encoding="utf-8") as file:
            self.unique_attendees = json.load(file)["unique_attendees"]
        self.comissioners = [att for att in self.unique_attendees if "Commissioner" in att or "President" in att]
        self.cabinet_members = [att for att in self.unique_attendees if "Commissioner" not in att and "President" not in att]


    def scrape(self, output_path="data/members"):
        chain = CabinetMemberMatchingChain(self.comissioners)
        print(f"\n\n---\n {self.cabinet_members[7]} \n---\n\n")
        print(f"\n\n---\n {chain.invoke(self.cabinet_members[7])} \n---\n\n")

