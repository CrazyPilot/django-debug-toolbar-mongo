import functools
import time
import inspect
import os

import django
from django.conf import settings

import pymongo
import pymongo.collection
import pymongo.cursor

__all__ = ['queries', 'inserts', 'updates', 'removes', 'install_tracker',
           'uninstall_tracker', 'reset']


_original_methods = {
    'insert': pymongo.collection.Collection.insert_one,
    'update': pymongo.collection.Collection.update_one,
    'remove': pymongo.collection.Collection.delete_one,
    'refresh': pymongo.cursor.Cursor._refresh,
}

queries = []
inserts = []
updates = []
removes = []


# Wrap Cursor._refresh for getting queries
# @functools.wraps(_original_methods['insert'])
# def _insert(collection_self, doc_or_docs, manipulate=True,
#            safe=False, check_keys=True, **kwargs):
#     start_time = time.time()
#     result = _original_methods['insert'](
#         collection_self,
#         doc_or_docs,
#         manipulate=manipulate,
#         safe=safe,
#         check_keys=check_keys,
#         **kwargs
#     )
#     total_time = (time.time() - start_time) * 1000
#
#     __traceback_hide__ = True
#     inserts.append({
#         'document': doc_or_docs,
#         'safe': safe,
#         'time': total_time,
#         'stack_trace': _get_stacktrace(),
#     })
#     return result

# Wrap Cursor._refresh for getting queries
# @functools.wraps(_original_methods['update'])
# def _update(collection_self, spec, document, upsert=False,
#            maniuplate=False, safe=False, multi=False, **kwargs):
#     start_time = time.time()
#     result = _original_methods['update'](
#         collection_self,
#         spec,
#         document,
#         upsert=upsert,
#         safe=safe,
#         multi=multi,
#         **kwargs
#     )
#     total_time = (time.time() - start_time) * 1000
#
#     __traceback_hide__ = True
#     updates.append({
#         'document': document,
#         'upsert': upsert,
#         'multi': multi,
#         'spec': spec,
#         'safe': safe,
#         'time': total_time,
#         'stack_trace': _get_stacktrace(),
#     })
#     return result

# Wrap Cursor._refresh for getting queries
# @functools.wraps(_original_methods['remove'])
# def _remove(collection_self, spec_or_id, safe=False, **kwargs):
#     start_time = time.time()
#     result = _original_methods['remove'](
#         collection_self,
#         spec_or_id,
#         safe=safe,
#         **kwargs
#     )
#     total_time = (time.time() - start_time) * 1000
#
#     __traceback_hide__ = True
#     removes.append({
#         'spec_or_id': spec_or_id,
#         'safe': safe,
#         'time': total_time,
#         'stack_trace': _get_stacktrace(),
#     })
#     return result

# Wrap Cursor._refresh for getting queries
@functools.wraps(_original_methods['refresh'])
def _cursor_refresh(cursor_self):
    # Look up __ private instance variables
    def privar(name):
        return getattr(cursor_self, '_Cursor__{0}'.format(name))

    print(f"{cursor_self.collection.full_name} {cursor_self._Cursor__spec}")

    # NOTE: See pymongo/cursor.py+557 [_refresh()] and
    # pymongo/message.py for where information is stored

    is_getmore = privar('id') is not None
    # Time the actual query
    start_time = time.time()
    result = _original_methods['refresh'](cursor_self)
    total_time = (time.time() - start_time) * 1000

    query_son = privar('query_spec')()

    __traceback_hide__ = True
    query_data = {
        'time': total_time,
        'operation': 'find',
        'stack_trace': None  #_get_stacktrace(),
    }

    if is_getmore:
        # getMore not query - move on
        query_data['cursor'] = id(cursor_self)
        query_data['operation'] = 'getmore'
        queries.append(query_data)
        return result

    # Collection in format <db_name>.<collection_name>
    collection_name = privar('collection')
    query_data['collection'] = collection_name.full_name.split('.')[1]

    if query_data['collection'] == '$cmd':
        # The query can be embedded within $query in some cases
        query_son = query_son.get("$query", query_son)

        query_data['operation'] = 'command'
        # Handle count as a special case
        if 'count' in query_son:
            # Information is in a different format to a standar query
            query_data['collection'] = query_son['count']
            query_data['operation'] = 'count'
            query_data['skip'] = query_son.get('skip')
            query_data['limit'] = abs(query_son.get('limit', 0))
            query_data['query'] = query_son['query']
        elif 'aggregate' in query_son:
            query_data['collection'] = query_son['aggregate']
            query_data['operation'] = 'aggregate'
            query_data['query'] = query_son['pipeline']
            query_data['skip'] = 0
            query_data['limit'] = None
    else:
        # Normal Query
        query_data['skip'] = privar('skip')
        query_data['limit'] = abs(privar('limit') or 0)
        query_data['query'] = query_son.get('$query') or query_son
        query_data['ordering'] = _get_ordering(query_son)
        query_data['cursor'] = id(cursor_self)

    queries.append(query_data)

    return result


def install_tracker():
    # if pymongo.collection.Collection.insert != _insert:
    #     pymongo.collection.Collection.insert = _insert
    # if pymongo.collection.Collection.update != _update:
    #     pymongo.collection.Collection.update = _update
    # if pymongo.collection.Collection.remove != _remove:
    #     pymongo.collection.Collection.remove = _remove
    if pymongo.cursor.Cursor._refresh != _cursor_refresh:
        pymongo.cursor.Cursor._refresh = _cursor_refresh


def uninstall_tracker():
    # if pymongo.collection.Collection.insert == _insert:
    #     pymongo.collection.Collection.insert = _original_methods['insert']
    # if pymongo.collection.Collection.update == _update:
    #     pymongo.collection.Collection.update = _original_methods['update']
    # if pymongo.collection.Collection.remove == _remove:
    #     pymongo.collection.Collection.remove = _original_methods['remove']
    if pymongo.cursor.Cursor._refresh == _cursor_refresh:
        pymongo.cursor.Cursor._refresh = _original_methods['cursor_refresh']


def reset():
    global queries, inserts, updates, removes
    queries = []
    inserts = []
    updates = []
    removes = []


def _get_ordering(son):
    """Helper function to extract formatted ordering from dict.
    """
    def fmt(field, direction):
        return '{0}{1}'.format({-1: '-', 1: '+'}[direction], field)

    if '$orderby' in son:
        return ', '.join(fmt(f, d) for f, d in son['$orderby'].items())
