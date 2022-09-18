import pymongo
import time
import json


class QueryTracker:

    _original_methods = {
        'refresh': pymongo.cursor.Cursor._refresh,
        'count_documents': pymongo.collection.Collection.count_documents,
        'insert_one': pymongo.collection.Collection.insert_one,
        'insert_many': pymongo.collection.Collection.insert_many,
        'update_one': pymongo.collection.Collection.update_one,
        'update_many': pymongo.collection.Collection.update_many,
        'replace_one': pymongo.collection.Collection.replace_one,
        'delete_one': pymongo.collection.Collection.delete_one,
        'delete_many': pymongo.collection.Collection.delete_many,
    }

    queries = []

    _cur_refresh_query = None
    _cur_refresh_cursor_hash = None

    @staticmethod
    def enable():
        pymongo.cursor.Cursor._refresh = QueryTracker._refresh
        pymongo.collection.Collection.count_documents = QueryTracker._count_documents
        pymongo.collection.Collection.insert_one = QueryTracker._insert_one
        pymongo.collection.Collection.insert_many = QueryTracker._insert_many
        pymongo.collection.Collection.update_one = QueryTracker._update_one
        pymongo.collection.Collection.update_many = QueryTracker._update_many
        pymongo.collection.Collection.replace_one = QueryTracker._replace_one
        pymongo.collection.Collection.delete_one = QueryTracker._delete_one
        pymongo.collection.Collection.delete_many = QueryTracker._delete_many

    @staticmethod
    def disable():
        pymongo.cursor.Cursor._refresh = QueryTracker._original_methods['refresh']
        pymongo.collection.Collection.count_documents = QueryTracker._original_methods['count_documents']
        pymongo.collection.Collection.insert_one = QueryTracker._original_methods['insert_one']
        pymongo.collection.Collection.insert_many = QueryTracker._original_methods['insert_many']
        pymongo.collection.Collection.update_one = QueryTracker._original_methods['update_one']
        pymongo.collection.Collection.update_many = QueryTracker._original_methods['update_many']
        pymongo.collection.Collection.replace_one = QueryTracker._original_methods['replace_one']

    @staticmethod
    def reset():
        QueryTracker.queries = []
        QueryTracker._cur_refresh_query = None
        QueryTracker._cur_refresh_cursor_hash = None

    @staticmethod
    def _profile_simple_op(name, collection: pymongo.collection.Collection, filter, *args, **kwargs):
        start_time = time.time()
        result = QueryTracker._original_methods[name](collection, filter, *args, **kwargs)
        total_time = (time.time() - start_time) * 1000
        QueryTracker.queries.append({
            'type': name,
            'collection': collection.full_name,
            'query': json.dumps(filter),
            'comment': kwargs.get('comment'),
            'time': total_time
        })
        return result

    @staticmethod
    def _count_documents(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('count_documents', collection, filter, *args, **kwargs)

    @staticmethod
    def _insert_one(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('insert_one', collection, filter, *args, **kwargs)

    @staticmethod
    def _insert_many(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('insert_many', collection, filter, *args, **kwargs)

    @staticmethod
    def _update_one(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('update_one', collection, filter, *args, **kwargs)

    @staticmethod
    def _update_many(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('update_many', collection, filter, *args, **kwargs)

    @staticmethod
    def _replace_one(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('replace_one', collection, filter, *args, **kwargs)

    @staticmethod
    def _delete_one(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('delete_one', collection, filter, *args, **kwargs)

    @staticmethod
    def _delete_many(collection: pymongo.collection.Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('delete_many', collection, filter, *args, **kwargs)

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
