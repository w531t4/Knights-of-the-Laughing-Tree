#!/bin/env python3


import json
import random
import logging
import logs


class Trivia:

    def __init__(self, loglevel=logging.INFO, question_file='qa.json', min_questions=0):
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
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
        self.logger.debug("type(self.raw)=" + str(type(self.raw)))
        for item in self.raw:
            self.logger.debug("type(item)=" + str(type(item)))
            self.logger.debug("item=" + str(item))
            if item['category'] not in db.keys():
                db[item['category']] = []
            db[item['category']].append(item)
        if removeDisqualifyingCategories:
            for cat in list(db):
                if len(db[cat]) < self.min_questions:
                    db.pop(cat)
        return db

    def selectRandomCategories(self, n, exclude=[], n_questions_per_category=-1):
        """Return n Topic Categories"""
        categories = [x for x in self.db.keys() if x not in exclude]
        self.logger.debug("categories = " + str(categories))
        if len(categories) < n:
            raise Exception("Cannot gather sufficient categories to cover request of", n)

        selected_categories = []
        while len(selected_categories) < n:
            r = random.randrange(0, len(categories))
            self.logger.debug("r=" + str(r) + " n=" + str(n) + " len(selected_categories)="
                              + str(len(selected_categories)))
            if categories[r] not in selected_categories:
                selected_categories.append(categories[r])
        self.logger.debug("selected_categories=" + str(selected_categories))
        if n_questions_per_category > 0:
            return_list = []
            for category in selected_categories:
                num_questions = len(self.db[category])
                self.logger.debug("num_questions=" + str(num_questions) +
                                  " n_questions_per_category=" + str(n_questions_per_category))
                if num_questions == n_questions_per_category:
                    return_list.append({"category": category, "topics": self.db[category]})
                    self.logger.debug("return_list=" + str(return_list))
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

