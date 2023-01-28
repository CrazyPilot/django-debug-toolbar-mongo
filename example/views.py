from django.conf import settings
from django.shortcuts import render
from contextlib import contextmanager
import time
import pymongo
from pymongo import MongoClient


collection = MongoClient(settings.MONGO_CONN)[settings.MONGO_DB][settings.MONGO_COLLECTION]


@contextmanager
def section(name):
    print('┌' + f' {name} '.center(80, '─'))
    yield
    print('└' + '─'*80)


@contextmanager
def timer():
    t = time.time()
    yield
    print(f" time: {(time.time() - t) * 1000} ms")


def get_list(iterable):
    with timer():
        print(f"items count: {len(list(iterable))}")


def index(request):
    with section('find one'):
        get_list(collection.find_one({'job.title': 'Developer'}, comment='find developers'))

    with section('count_documents'):
        with timer():
            collection.count_documents({'name': 'Alice'}, comment='count_documents')

    with section('find 1'):
        get_list(collection.find({'name': 'Alice'}, comment='find 1'))

    with section('find 2'):
        get_list(collection.find({'name': 'Alice'}, comment='find 2'))

    with section('find one'):
        with timer():
            collection.find_one({'idx': 25}, comment='find one')

    with section('find projection'):
        get_list(collection.find({'job.title': 'Developer'}, {'job': 1}, comment='find projection'))

    with section('find all'):
        get_list(collection.find(comment='find all'))

    with section('find ordered'):
        get_list(collection.find({'job.title': 'Developer'}, comment='find ordered').sort('age', -1))

    with section('find ordered partly index'):
        get_list(collection.find({'job.title': 'Developer', 'name': 'Bob'}, comment='find ordered partly index').sort('age', -1))

    with section('find ordered in memory'):
        get_list(collection.find({'job.title': 'Developer'}, comment='find ordered in memory').sort('job.salary', -1))

    with section('find covered by index'):
        get_list(collection.find({'job.title': 'Developer'}, {'_id': 0, 'job.title': 1, 'age': 1}, comment='find covered by index').sort('age', -1))

    with section('find skip limit'):
        get_list(collection.find({'job.title': 'Developer'}, comment='find skip limit').skip(20).limit(50))

    with section('find complicated query'):
        get_list(collection.find({'job.title': 'Developer', 'age': {'$gte': 30, '$lte': 40}}, comment='find complicated query'))

    with section('update_many'):
        with timer():
            collection.update_many({'name': "Alice"}, {'$set': {'job.salary': 3500}}, comment='update_many')

    with section('aggregate'):
        get_list(collection.aggregate([
             {
                '$project': {
                    'food': 0
                }
            }, {
                '$set': {
                    'money': '$job.salary'
                }
            }
        ], comment='aggregate'))

    return render(request, 'index.html')

