import pymongo
import time
import json


class QueryTracker:
    _original_methods = {
        'count_documents': pymongo.collection.Collection.count_documents,
        'find': pymongo.collection.Collection.find,
        'refresh': pymongo.cursor.Cursor._refresh,
    }

    queries = []

    _cur_refresh_query = None
    _cur_refresh_cursor_id = None

    @staticmethod
    def install():
        pymongo.collection.Collection.count_documents = QueryTracker.count_documents
        pymongo.collection.Collection.find = QueryTracker.find
        pymongo.cursor.Cursor._refresh = QueryTracker.refresh

    @staticmethod
    def reset():
        QueryTracker.queries = []
        QueryTracker._cur_refresh_query = None
        QueryTracker._cur_refresh_cursor_id = None

    @staticmethod
    def count_documents(collection: pymongo.collection.Collection, filter, *args, **kwargs):
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
    def refresh(cursor: pymongo.cursor.Cursor):
        start_time = time.time()
        result = QueryTracker._original_methods['refresh'](cursor)
        total_time = (time.time() - start_time) * 1000

        if cursor.cursor_id and QueryTracker._cur_refresh_cursor_id != cursor.cursor_id:
            # на обработку пришел новый запрос

            # если есть инфа по предыдущему запросу, то сохраняем ее
            QueryTracker.save_last_refresh_query()

            QueryTracker._new_refresh_query(cursor, total_time)
            # QueryTracker._cur_refresh_cursor_id = cursor.cursor_id
            # QueryTracker._cur_refresh_query = {
            #     'type': 'find',
            #     'collection': cursor.collection.full_name,
            #     'query': json.dumps(cursor._Cursor__spec),
            #     'projection': cursor._Cursor__projection,
            #     'ordering': cursor._Cursor__ordering.to_dict() if cursor._Cursor__ordering else cursor._Cursor__ordering,
            #     'skip': cursor._Cursor__skip,
            #     'limit': cursor._Cursor__limit,
            #     'time': total_time
            # }
        elif QueryTracker._cur_refresh_query:
            # этот курсор - продолжение предыдущего запроса
            QueryTracker._cur_refresh_query['time'] += total_time
        else:
            # это новый курсор, но без cursor_id, курсор выполнился за 1 запрос
            QueryTracker._new_refresh_query(cursor, total_time)

        if not cursor.alive:
            # курсор отработал - можно сохранять данные в массив
            QueryTracker.queries.append(QueryTracker._cur_refresh_query)
            QueryTracker._cur_refresh_query = None
            QueryTracker._cur_refresh_cursor_id = None

        return result

    @staticmethod
    def _new_refresh_query(cursor, total_time):
        QueryTracker._cur_refresh_cursor_id = cursor.cursor_id
        QueryTracker._cur_refresh_query = {
            'type': 'find',
            'collection': cursor.collection.full_name,
            'query': json.dumps(cursor._Cursor__spec),
            'projection': cursor._Cursor__projection,
            'ordering': cursor._Cursor__ordering.to_dict() if cursor._Cursor__ordering else cursor._Cursor__ordering,
            'skip': cursor._Cursor__skip,
            'limit': cursor._Cursor__limit,
            'time': total_time
        }

    @staticmethod
    def save_last_refresh_query():
        # TODO  этот метод уже не нужен, можно удалять
        if QueryTracker._cur_refresh_query:
            raise Exception('Такого быть не должно')
            QueryTracker.queries.append(QueryTracker._cur_refresh_query)

    @staticmethod
    def find(collection: pymongo.collection.Collection, query, *args, **kwargs):
        start_time = time.time()
        result = QueryTracker._original_methods['find'](collection, query, *args, **kwargs)
        total_time = (time.time() - start_time) * 1000
        return result