import pymongo
import time


_original_methods = {
    'count_documents': pymongo.collection.Collection.count_documents,
    'refresh': pymongo.cursor.Cursor._refresh,
}

queries = []

_current_refresh = None
_current_cursor_id = None


def install():
    pymongo.collection.Collection.count_documents = count_documents
    pymongo.cursor.Cursor._refresh = refresh


def reset():
    queries = []


def count_documents(collection: pymongo.collection.Collection, filter, *args, **kwargs):
    start_time = time.time()
    result = _original_methods['count_documents'](collection, filter,  *args, **kwargs)
    total_time = time.time() - start_time
    queries.append({
        'type': 'count_documents',
        'collection': collection.full_name,
        'query': filter,
        'time': total_time * 1000
    })
    return result


def refresh(cursor: pymongo.cursor.Cursor):
    start_time = time.time()
    result = _original_methods['refresh'](cursor)
    total_time = (time.time() - start_time)

    print(f"#{cursor.cursor_id} {cursor.collection.full_name}")
    print(f"query: {cursor._Cursor__spec}")
    print(f"projection: {cursor._Cursor__projection}")
    print(f"ordering: {cursor._Cursor__ordering.to_dict() if cursor._Cursor__ordering else None}")
    print(f"skip: {cursor._Cursor__skip}")
    print(f"limit: {cursor._Cursor__limit}")
    print(f"time: {total_time * 1000} ms")
    print('-' * 10)
    return result