#!/bin/env python3


import json
import random


class Trivia:

    def __init__(self, question_file='qa.json', min_questions=0):
        # read contents of question list
        self.debug = False
        self.raw = self.readQuestionFile(question_file)
        self.min_questions = min_questions
        self.db = {}
        self.db = self.assemble_db()

        pass
    def __len__(self):
        return len(self.raw)

    def readQuestionFile(self, question_file):
        with open(question_file) as fr:
            a = "".join(fr.readlines())
            if self.debug: print(a)
            return list(json.loads(a))
            #return list(json.loads("".join(fr.readlines())))

    def assemble_db(self, removeDisqualifyingCategories=True):
        """Consolidate JSON-oriented Quester/Answer File into a Dictionary"""
        # rather than read the file multiple times, we convert to a dictionary first
        db = {}
        if self.debug: print(type(self.raw))
        for item in self.raw:
            if self.debug: print(type(item))
            if self.debug: print(item)
            if item['category'] not in db.keys():
                db[item['category']] = []
            db[item['category']].append(item)
        if removeDisqualifyingCategories:
            for cat in db.keys():
                if len(db[cat]) < self.min_questions:
                    db.pop(cat)
        return db

    def selectRandomCategories(self, n, exclude=[], n_questions_per_category=-1):
        """Return n Topic Categories"""
        categories = [x for x in self.db.keys() if x not in exclude]
        if self.debug: print("selectRandomCategories(): categories = ", categories)
        if len(categories) < n:
            raise Exception("Cannot gather sufficient categories to cover request of", n)

        selected_categories = []
        while len(selected_categories) < n:
            r = random.randrange(0, len(categories))
            if self.debug: print("selectRandomCategories(): r= ", r, "n=", n, "len(selected_categories)=", len(selected_categories))
            if categories[r] not in selected_categories:
                selected_categories.append(categories[r])
        if self.debug: print("selectRandomCategories(): selected_categories=", selected_categories)
        if n_questions_per_category > 0:
            return_list = []
            for category in selected_categories:
                num_questions = len(self.db[category])
                if self.debug: print("selectRandomCategories(): num_questions=", num_questions, "n_questions_per_category=", n_questions_per_category)
                if num_questions == n_questions_per_category:
                    return_list.append({"category": category, "topics": self.db[category]})
                    if self.debug: print("selectRandomCategories(): return_list=", return_list)
                else:
                    hitlist = []
                    selection = []
                    while len(hitlist) < num_questions:
                        r = random.randrange(0,num_questions)
                        if r not in hitlist:
                            hitlist.append(r)
                            selection.append(self.db[category][r])
                    return_list.append({"category": category, "topics": selection})
            return return_list
        else:
            return [{"category": x, "topics": self.db[x]} for x in selected_categories]

