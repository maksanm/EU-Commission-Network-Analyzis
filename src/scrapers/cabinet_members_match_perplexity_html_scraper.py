from dotenv import load_dotenv
load_dotenv()

import json
import os
import re
from os import path
from chains.cabinet_member_matching_chain import CabinetMemberMatchingChain


class CabinetMembersMatchScraper:


    def __init__(self):
        with open(os.getenv("UNIQUE_ATTENDEES_PATH"), encoding="utf-8") as file:
            self.unique_attendees = json.load(file)["unique_attendees"]
        self.comissioners = [att for att in self.unique_attendees if "Commissioner" in att or "President" in att]

        # Extract cabinet members using the regex pattern to capture the full name before the parentheses
        name_pattern = re.compile(r"^(.*?)\s*\(")
        cabinet_members_filtered = [
            (att, name_pattern.match(att).group(1))
            for att in self.unique_attendees
            if "Cabinet member" in att
        ]
        self.cabinet_members, self.cabinet_member_names = zip(*cabinet_members_filtered) if cabinet_members_filtered else ([], [])


    def scrape(self, output_path=os.getenv("CABINET_MEMBERS_MATCH_PATH")):
        chain = CabinetMemberMatchingChain(self.comissioners)

        # If cabinet_members_match.json exists, load already matched cabinet members from it
        if path.exists(output_path):
            with open(output_path, encoding="utf-8") as file:
                cabinet_members_match_dict = json.load(file)
        else:
            cabinet_members_match_dict = {}

        # Invoke chain for each cabinet member
        for i, cabinet_member in enumerate(self.cabinet_members):
            if cabinet_member in cabinet_members_match_dict:
                continue
            print(f"Scraping Commisioner for {self.cabinet_member_names[i]}...")
            cabinet_members_match_dict = cabinet_members_match_dict | {cabinet_member: chain.invoke(self.cabinet_member_names[i])["commissioner"]}
            print(f"Finished scraping: \"{cabinet_member}\": \"{cabinet_members_match_dict[cabinet_member]}\"")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cabinet_members_match_dict, f, ensure_ascii=False, indent=4)
        print(f"Saved matching dictionary to cabinent_members_match.json")


# Example usage
if __name__ == "__main__":
    scraper = CabinetMembersMatchScraper()
    scraper.scrape()
