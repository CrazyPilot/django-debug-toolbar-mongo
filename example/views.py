from django.shortcuts import render

import pymongo
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/?readPreference=primary&ssl=false")
db = client.debug_test


def index(request):
    #list(db.test.find({'name': 'test'}))
    db.test.count_documents({'name': 'test'})
    db.test.count_documents({'name': 'test'})
    list(db.test.find({'name': 'test', 'age': {'$lt': 134234}}).skip(1))
    db.test.count_documents({'name': 'test'})
    list(db.test.find({'name': 'test'}).sort('name'))
    sort_fields = [('name', pymongo.DESCENDING), ('date', pymongo.ASCENDING)]
    list(db.test.find({'name': 'test'}).sort(sort_fields))
    list(db.test.find({
        '$or': [
            {
                'age': {'$lt': 50, '$gt': 18},
                'paying': True,
            },
            {
                'name': 'King of the world',
                'paying': False,
            }
        ]
    }))
    db.test.insert_one({'name': 'test'})
    db.test.insert_one({'name': 'test2'})
    db.test.update_one({'name': 'test2'}, {'$set': {'age': 1}}, upsert=True)
    db.test.delete_one({'name': 'test1'})
    return render(request, 'index.html')

