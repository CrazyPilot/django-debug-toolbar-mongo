import pymongo
import time
import json


class QueryTracker:
    _original_methods = {
        'count_documents': pymongo.collection.Collection.count_documents,
        'refresh': pymongo.cursor.Cursor._refresh,
    }

    queries = []

    _cur_refresh_query = None
    _cur_refresh_cursor_hash = None

    @staticmethod
    def enable():
        pymongo.collection.Collection.count_documents = QueryTracker._count_documents
        pymongo.cursor.Cursor._refresh = QueryTracker._refresh

    @staticmethod
    def disable():
        if pymongo.collection.Collection.count_documents == QueryTracker._count_documents:
            pymongo.collection.Collection.count_documents = QueryTracker._original_methods['count_documents']
        if pymongo.cursor.Cursor._refresh == QueryTracker._refresh:
            pymongo.cursor.Cursor._refresh = QueryTracker._original_methods['refresh']

    @staticmethod
    def reset():
        QueryTracker.queries = []
        QueryTracker._cur_refresh_query = None
        QueryTracker._cur_refresh_cursor_hash = None

    @staticmethod
    def _count_documents(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        start_time = time.time()
        result = QueryTracker._original_methods['count_documents'](collection, filter,  *args, **kwargs)
        total_time = (time.time() - start_time) * 1000
        QueryTracker.queries.append({
            'type': 'count_documents',
            'collection': collection.full_name,
            'query': json.dumps(filter),
            'time': total_time
        })
        return result

    @staticmethod
    def _refresh(cursor: pymongo.cursor.Cursor):
        start_time = time.time()
        result = QueryTracker._original_methods['refresh'](cursor)
        total_time = (time.time() - start_time) * 1000

        cursor_hash = QueryTracker._cursor_to_hash(cursor)

        if cursor_hash == QueryTracker._cur_refresh_cursor_hash:
            # это продолжение запроса, увеличиваем таймер
            QueryTracker._cur_refresh_query['time'] += total_time
        else:
            # это новый запрос - создаем его
            QueryTracker._save_last_refresh_query()  # сохранили старый, если есть
            QueryTracker._new_refresh_query(cursor, total_time)

        # это последний кусок запроса и его нужно сохранить
        if not cursor.alive:
            QueryTracker._save_last_refresh_query()  # сохранили старый, если есть

        return result

    @staticmethod
    def _cursor_to_dict(cursor):
        return {
            'collection': cursor.collection.full_name,
            'query': json.dumps(cursor._Cursor__spec),
            'projection': cursor._Cursor__projection,
            'ordering': cursor._Cursor__ordering.to_dict() if cursor._Cursor__ordering else cursor._Cursor__ordering,
            'skip': cursor._Cursor__skip,
            'limit': cursor._Cursor__limit,
            'comment': cursor._Cursor__comment,
        }

    @staticmethod
    def _cursor_to_hash(cursor):
        d = QueryTracker._cursor_to_dict(cursor)
        return json.dumps(d)

    @staticmethod
    def _new_refresh_query(cursor, total_time):
        QueryTracker._cur_refresh_cursor_hash = QueryTracker._cursor_to_hash(cursor)
        QueryTracker._cur_refresh_query = {
            'type': 'find',
            'time': total_time
        }
        QueryTracker._cur_refresh_query.update(QueryTracker._cursor_to_dict(cursor))

    @staticmethod
    def _save_last_refresh_query():
        if QueryTracker._cur_refresh_query:
            # у нас осталась инфа про предыдущий запрос - надо его сохранить
            QueryTracker.queries.append(QueryTracker._cur_refresh_query)
            QueryTracker._cur_refresh_query = None
            QueryTracker._cur_refresh_cursor_hash = None
