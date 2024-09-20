import pymongo
from pymongo.synchronous.collection import Collection
import time
import json
import bson.json_util

from django.conf import settings


EXPLAIN_ENABLED = getattr(settings, 'DEBUG_TOOLBAR_MONGO_EXPLAIN', False)


# def son_to_pymongo(son: SON):
#     if not son:
#         return None
#     result = []
#     for key, val in son.to_dict().items():
#         result.append((key, val))
#     return result


class MongoIndexInfo:
    collections = {}

    @classmethod
    def index_info(cls, collection: Collection, index_name):
        if collection.name not in cls.collections:
            cls.collections[collection.name] = collection.index_information()
        return cls.collections[collection.name][index_name]['key']


class QueryTracker:

    _original_methods = {
        'refresh': pymongo.cursor.Cursor._refresh,
        'count_documents': Collection.count_documents,
        'insert_one': Collection.insert_one,
        'insert_many': Collection.insert_many,
        'update_one': Collection.update_one,
        'update_many': Collection.update_many,
        'replace_one': Collection.replace_one,
        'delete_one': Collection.delete_one,
        'delete_many': Collection.delete_many,
        'aggregate': Collection.aggregate,
    }

    queries = []

    _cur_refresh_query = None
    _cur_refresh_cursor_hash = None

    @staticmethod
    def enable():
        pymongo.cursor.Cursor._refresh = QueryTracker._refresh
        Collection.count_documents = QueryTracker._count_documents
        Collection.insert_one = QueryTracker._insert_one
        Collection.insert_many = QueryTracker._insert_many
        Collection.update_one = QueryTracker._update_one
        Collection.update_many = QueryTracker._update_many
        Collection.replace_one = QueryTracker._replace_one
        Collection.delete_one = QueryTracker._delete_one
        Collection.delete_many = QueryTracker._delete_many
        Collection.aggregate = QueryTracker._aggregate

    @staticmethod
    def disable():
        pymongo.cursor.Cursor._refresh = QueryTracker._original_methods['refresh']
        Collection.count_documents = QueryTracker._original_methods['count_documents']
        Collection.insert_one = QueryTracker._original_methods['insert_one']
        Collection.insert_many = QueryTracker._original_methods['insert_many']
        Collection.update_one = QueryTracker._original_methods['update_one']
        Collection.update_many = QueryTracker._original_methods['update_many']
        Collection.replace_one = QueryTracker._original_methods['replace_one']
        Collection.delete_one = QueryTracker._original_methods['delete_one']
        Collection.delete_many = QueryTracker._original_methods['delete_many']
        Collection.aggregate = QueryTracker._original_methods['aggregate']

    @staticmethod
    def reset():
        QueryTracker.queries = []
        QueryTracker._cur_refresh_query = None
        QueryTracker._cur_refresh_cursor_hash = None

    @staticmethod
    def _profile_simple_op(name, collection: Collection, filter, *args, **kwargs):
        QueryTracker._save_last_refresh_query()  # сохранили последний find, тк начался другой запрос

        start_time = time.time()
        result = QueryTracker._original_methods[name](collection, filter, *args, **kwargs)
        total_time = (time.time() - start_time) * 1000

        explain = {}
        if EXPLAIN_ENABLED:
            if name not in ['aggregate', 'insert_one', 'insert_many']:
                QueryTracker.disable()
                # limit добавил тут, чтобы запрос выполнился быстрее
                raw_explain = collection.find(filter).limit(100)
                if hint := kwargs.get('hint'):
                    raw_explain = raw_explain.hint(hint)
                raw_explain = raw_explain.explain()
                explain = QueryTracker._analyze_raw_explain(raw_explain, collection, filter)
                print(f" 🔍 Explain {collection.name}:{kwargs.get('comment', '')}")
                QueryTracker.enable()

        QueryTracker.queries.append({
            'type': name,
            'collection': collection.full_name,
            'query': bson.json_util.dumps(filter),
            'comment': kwargs.get('comment'),
            'hint': kwargs.get('hint'),
            'time': total_time,
            'explain': explain
        })
        return result

    @staticmethod
    def _count_documents(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('count_documents', collection, filter, *args, **kwargs)

    @staticmethod
    def _insert_one(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('insert_one', collection, filter, *args, **kwargs)

    @staticmethod
    def _insert_many(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('insert_many', collection, filter, *args, **kwargs)

    @staticmethod
    def _update_one(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('update_one', collection, filter, *args, **kwargs)

    @staticmethod
    def _update_many(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('update_many', collection, filter, *args, **kwargs)

    @staticmethod
    def _replace_one(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('replace_one', collection, filter, *args, **kwargs)

    @staticmethod
    def _delete_one(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('delete_one', collection, filter, *args, **kwargs)

    @staticmethod
    def _delete_many(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('delete_many', collection, filter, *args, **kwargs)

    @staticmethod
    def _aggregate(collection: Collection, filter, *args, **kwargs):
        return QueryTracker._profile_simple_op('aggregate', collection, filter, *args, **kwargs)

    @staticmethod
    def _refresh(cursor: pymongo.cursor.Cursor):
        cursor_hash = QueryTracker._cursor_to_hash(cursor)
        if cursor_hash != QueryTracker._cur_refresh_cursor_hash:
            # это новый запрос -- делаем эксплэйн до выполнения запроса
            explain = QueryTracker._explain_last_refresh_query(cursor)

        start_time = time.time()
        result = QueryTracker._original_methods['refresh'](cursor)
        total_time = (time.time() - start_time) * 1000

        if cursor_hash == QueryTracker._cur_refresh_cursor_hash:
            # это продолжение запроса, увеличиваем таймер
            QueryTracker._cur_refresh_query['time'] += total_time
        else:
            # это новый запрос - создаем его
            QueryTracker._save_last_refresh_query()  # сохранили старый, если есть
            QueryTracker._new_refresh_query(cursor, total_time)
            QueryTracker._cur_refresh_query['explain'] = explain  # добавляем explain в инфу о новом запросе

        # это последний кусок запроса и его нужно сохранить
        if not cursor.alive:
            QueryTracker._save_last_refresh_query()  # сохранили старый, если есть

        return result

    @staticmethod
    def _cursor_to_dict(cursor):
        # if type(cursor._Cursor__ordering) is dict:
        #     ordering = cursor._Cursor__ordering
        # elif cursor._Cursor__ordering:
        #     ordering = cursor._Cursor__ordering.to_dict()  # It works for pymongo < 4.7
        # else:
        #     ordering = None
        return {
            'collection': cursor.collection.full_name,
            'query': bson.json_util.dumps(cursor._spec),
            'projection': cursor._projection,
            # 'ordering': cursor._Cursor__ordering.to_dict() if cursor._Cursor__ordering else cursor._Cursor__ordering,
            # 'ordering': ordering,
            'ordering': cursor._ordering,
            'skip': cursor._skip,
            'limit': cursor._limit,
            'comment': cursor._comment,
            'hint': cursor._hint,
        }

    @staticmethod
    def _cursor_to_hash(cursor):
        d = QueryTracker._cursor_to_dict(cursor)
        return bson.json_util.dumps(d)

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

    @staticmethod
    def _explain_last_refresh_query(cursor: pymongo.cursor.Cursor):
        # запускаем explain
        explain = {}
        if EXPLAIN_ENABLED and cursor:
            QueryTracker.disable()
            _query = cursor._spec
            _project = cursor._projection
            _sort = cursor._ordering
            _skip = cursor._skip
            _limit = cursor._limit
            _hint = cursor._hint
            _request = cursor.collection.find(_query, _project)
            if _sort:
                _request = _request.sort(_sort)  # _request.sort(list(_sort))
            if _hint:
                _request = _request.hint(_hint)
            raw_explain = _request.skip(_skip).limit(_limit).explain()
            print(f" 🔍 Explain {cursor.collection.name}:{cursor._comment}")
            explain = QueryTracker._analyze_raw_explain(raw_explain, cursor.collection, _query, _sort)
            QueryTracker.enable()
        # QueryTracker._cur_refresh_query['explain'] = explain
        return explain

    @staticmethod
    def _analyze_raw_explain(raw_explain, collection: Collection, query_filter=None, query_sort=None):
        """
        COLLSCAN -- не нашли никакого индекса (плохо)
        IXSCAN GEO_NEAR_2DSPHERE -- нашли индекс (надо проверить покрытие)
        SORT -- сортировка в памяти (плохо)

        When an index covers a query, the explain result has an IXSCAN stage that is not a descendant of a FETCH stage,
        and in the executionStats, the
        explain.executionStats.totalDocsExamined is 0.
        """
        stage = raw_explain['queryPlanner']['winningPlan']
        stage_types = []  # этапы выполнения запроса
        indexes = set()
        while stage:
            if 'queryPlan' in stage:
                print("=== Weird winningPlan structure ===")
                print(json.dumps(raw_explain['queryPlanner']['winningPlan'], indent=2))
                print("=== /Weird winningPlan structure ===")
                stage = stage['queryPlan']
            stage_types.append(stage['stage'])
            if stage['stage'] in ['IXSCAN', 'GEO_NEAR_2DSPHERE']:
                indexes.add(stage['indexName'])
            stage = stage['inputStage'] if 'inputStage' in stage else None
        stage_types.reverse()  # чтобы этапы шли по порядку
        indexes = list(indexes)

        index_intel = {}
        if len(indexes) == 1:
            index_intel['state'] = 'OK'
            index_intel['name'] = indexes[0]

            # инфа о полях, кторые используются в индексе
            index_info = MongoIndexInfo.index_info(collection, indexes[0])

            # собираем список полей, которые участвуют в запросе
            fields_in_query = []
            if query_filter:
                for field, _ in query_filter.items():
                    fields_in_query.append(field)
            if query_sort:
                for field, _ in query_sort.items():
                    fields_in_query.append(field)

            # Список полей индекса и инфа о том, используется-ли это поле
            index_coverage = []
            _covered = True
            _index_covered_fields = []  # список полей, которые покрыты индексом
            for index_key, index_type in index_info:
                if index_key not in fields_in_query:
                    _covered = False  # если хоть одно поле пропустили, то дальше они уже не юзаются
                index_coverage.append({
                    'key': index_key,
                    'type': index_type,
                    'covered': _covered
                })
                if _covered:
                    _index_covered_fields.append(index_key)
            index_intel['index_coverage'] = index_coverage

            # покрытие запроса к монге индексом
            query_coverage = []
            for query_key in fields_in_query:
                _covered = query_key in _index_covered_fields
                if not _covered:
                    index_intel['state'] = 'PARTIAL'  # индекс частично покрыл запрос
                query_coverage.append({
                    'key': query_key,
                    'covered': _covered
                })
            index_intel['query_coverage'] = query_coverage

        elif len(indexes) == 0:
            index_intel['state'] = 'NOT_USED'
        else:
            index_intel['state'] = 'COMPLICATED'  # использовалось несколько индексов -- разибарайся с ними сам

        result = {
            'covered_by_index': len(indexes) == 1 and 'FETCH' not in stage_types,  # покрыто индексом
            'sorted_in_memory': 'SORT' in stage_types,
            'index_intel': index_intel,
            'raw': raw_explain,
            'stages': stage_types,
            'indexes': indexes,
        }

        return result
