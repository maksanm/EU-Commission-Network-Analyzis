import networkx as nx
from os import listdir
from os.path import isfile, join
import json
import os
from itertools import combinations
from root_pointer import ROOT
MEETINGS_DIR = join(ROOT, os.getenv("MEETINGS_PATH"))
COMMISIONERS_DATA_DIR = join(ROOT, os.getenv("COMMISSIONERS_DATA_PATH"))
MATCH_DATA_DIR = join(ROOT, os.getenv("CABINET_MEMBERS_MATCH_PATH"))
UNREALTED_TITLES = [
    "Director-General",
    "Head of Task Force",
    "Acting Director-General",
    "High Representative",
    "Director",
    "Secretary-General",
    "Head of service",
    "the Chair of the Regulatory Scrutiny Board",
    "Acting Head of Service",
    "Acting Head of service",
    "Head of Service",
    "Director of Office",
    "Acting  Head of service"
]

def meetings_file_generator():
    for file in listdir(MEETINGS_DIR):
        file = join(MEETINGS_DIR, file)
        if isfile(file):
            yield file

def create_graph_with_members() -> nx.Graph:
    graph = nx.Graph()
    with open(COMMISIONERS_DATA_DIR, "r", encoding="utf8") as f:
        data = json.load(f)["commissioners"]

    for commissioner in data:
        name = commissioner["name"]
        del commissioner["name"]
        graph.add_node(name, **commissioner)
    return graph

def all_members_list():
    with open(COMMISIONERS_DATA_DIR, "r", encoding="utf8") as f:
        data = json.load(f)["commissioners"]
    result = [elem["name"] for elem in data]
    return result

def members_match():
    with open(MATCH_DATA_DIR, "r", encoding="utf8") as f:
        return json.load(f)

def extract_all_unique_members(file):
    if "__unique_attendees.json" in file:
        return None
    with open(file, "r", encoding="utf8") as f:
        data = json.load(f)["meetings"]
    unique_attendees = set()
    for meeting in data:
        for attendee in meeting:
            unique_attendees.add(attendee)

    result = set()
    members_list = all_members_list()
    match = members_match()
    for attendee in unique_attendees:
        if attendee in members_list:
            result.add(attendee)
        else:
            try:
                result.add(match[attendee])
            except KeyError:
                if attendee.split("(")[1].replace(")", "") in UNREALTED_TITLES:
                    pass
                elif "Joseph Vella" in attendee or "Fiona Knab-Lunny" in attendee:
                    pass
                else:
                    print(f"missing {attendee}")
    return result

def create_edges_for_meeting(file, graph: nx.Graph):
    if "__unique_attendees.json" in file:
        return None
    attendees = extract_all_unique_members(file)
    for combination in combinations(attendees, 2):
        a1, a2 = combination
        if graph.has_edge(a1, a2):
            graph[a1][a2]["weight"] += 1
        else:
            graph.add_edge(a1, a2, weight=1)

def create_all_edges(graph: nx.Graph):
    for file in meetings_file_generator():
        create_edges_for_meeting(file, graph)
    graph.remove_node("UNKNOWN")
    return graph


def create_full_graph():
    graph = create_graph_with_members()
    return create_all_edges(graph)



if __name__ == '__main__':
    print(create_full_graph())
