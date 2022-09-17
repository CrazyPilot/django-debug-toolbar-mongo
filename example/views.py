from django.shortcuts import render
from contextlib import contextmanager
import time
import pymongo
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/?readPreference=primary&ssl=false")
db = client.debug_test


@contextmanager
def section(name):
    print('┌' + f' {name} '.center(80, '─'))
    yield
    print('└' + '─'*80)


def get_list(iterable):
    t = time.time()
    print(f"items count: {len(list(iterable))}")
    print(f"for loop time: {(time.time() - t) * 1000} ms")


def index(request):
    with section('test'):
        db.test.count_documents({'name': 'test'})

    print('2')
    db.test.count_documents({'name': 'test'})

    print('3')
    list(db.test.find({'name': 'test', 'age': {'$lt': 134234}}).skip(1))

    print('4')
    db.test.count_documents({'name': 'test'})

    print('5')
    list(db.test.find({'name': 'test'}).sort('name'))

    print('6')
    sort_fields = [('name', pymongo.DESCENDING), ('date', pymongo.ASCENDING)]
    list(db.test.find({'name': 'test'}).sort(sort_fields))

    print('7')
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

    print('8')
    db.test.insert_one({'name': 'test'})

    print('9')
    db.test.insert_one({'name': 'test2'})

    print('10')
    db.test.update_one({'name': 'test2'}, {'$set': {'age': 1}}, upsert=True)

    print('11')
    db.test.delete_one({'name': 'test1'})
    return render(request, 'index.html')

