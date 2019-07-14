#!/bin/env python3


import json
import random


class Trivia:

    def __init__(self, question_file='qa.json', min_questions=0):
        # read contents of question list
        self.raw = self.readQuestionFile(question_file)
        self.min_questions = min_questions
        self.db = self.assemble_db()
        pass

    def readQuestionFile(self, question_file):
        with open(question_file) as fr:
            return list(json.loads(fr.readlines()))

    def assemble_db(self, removeDisqualifyingCategories=True):
        """Consolidate JSON-oriented Quester/Answer File into a Dictionary"""
        # rather than read the file multiple times, we convert to a dictionary first
        db = {}
        for item in self.raw:
            if item.category not in self.db.keys():
                self.db[item.category] = []
            db[item.category].append(item)

        if removeDisqualifyingCategories:
            for cat in db.keys():
                if len(db[cat]) < self.min_questions:
                    db.pop(cat)
        return db

    def selectRandomCategories(self, n, exclude=[], n_questions_per_category=-1):
        """Return n Topic Categories"""
        categories = [x for x in self.db.keys() if x not in exclude]
        if len(categories) < n:
            raise Exception("Cannot gather sufficient categories to cover request of", n)

        selected_categories = []
        while len(selected_categories) < n:
            r = random.randrange(0, len(categories))
            if categories[r] not in selected_categories:
                selected_categories.append(categories[r])

        if n_questions_per_category > 0:
            return_list = []
            for category in selected_categories:
                num_questions = len(self.db[category])
                if num_questions == n_questions_per_category:
                    return_list.append({"category": category, "topics": self.db[category]})
                else:
                    hitlist = []
                    selection = []
                    while hitlist < num_questions:
                        r = random.randrange(0,num_questions)
                        if r not in hitlist:
                            hitlist.append(r)
                            selection.append(self.db[category][r])
                    return_list.append({"category": category, "topics": selection})
        else:
            return [{"category": x, "topics": self.db[x]} for x in selected_categories]

