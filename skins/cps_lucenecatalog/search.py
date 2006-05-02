##parameters=query={}, sort_by=None, direction=None, hide_folder=0, folder_prefix=None, start_date=None, end_date=None, default_languages=0, allow_empty_search=0, sort_limit=100, REQUEST=None
# $Id: search.py 31200 2006-01-02 18:57:14Z fguillaume $
"""
Return a list of brains matching the query.

Examples:

# Get all the News Item documents in the portal
brains = portal.search(query={'portal_type': ('News Item',)})
for brain in brains:
    proxy = brain.getObject()
    document = proxy.getContent()
    ...

# Get all the Italian News Item and Italian Press Release documents
# in the portal
brains = portal.search(query={'portal_type': ('News Item', 'Press Release'),
                              'Languages': 'it'})

# Get all the published News Item documents in the portal which contains the
# text "mycomparny.com".
brains = portal.search(query={'SearchableText': 'mycompany.com',
                              'portal_type': ('News Item',),
                              'review_state': 'published',
                       }
                      )

# Get all the documents in the portal which are located below the folder
# "folder1" which is located in the "workspaces" folder.
brains = portal.search(query={'path': '/cps/workspaces/folder1'})
# if you know only the relative path:
brains = portal.search(folder_prefix='workspaces/folder1',
                       allow_empty_search=1,
                      )

# the 2 previous searches will return all the documents that are pointed by
# proxies that are located below the folder1,
# this means that if you have a proxy that contains 3 translations you
# will have 3 brains for this proxy.
# If you want only a list of proxies in their default languages without
# the available translation:
brains = portal.search(query={'path': '/cps/workspaces/folder1'},
                       default_languages=1)

"""

from zLOG import LOG, DEBUG, INFO

from Products.ZCTextIndex.ParseTree import ParseError
ParseErrors = (ParseError,)
try:
    from Products.TextIndexNG2.BaseParser import QueryParserError
    ParseErrors += (QueryParserError,)
except ImportError:
    pass


catalog = context.portal_catalog

if REQUEST is not None:
    query.update(REQUEST.form)

for k, v in query.items():
    if not v or same_type(v, []) and not filter(None, v):
        del query[k]

# Size of the batch
if not query.has_key('b_size'):
    query['b_size'] = 10

# Start of the batch
if not query.has_key('b_start'):
    query['b_start'] = 0


if str(query.get('modified')) == '1970/01/01':
    del query['modified']
    if query.has_key('modified_usage'):
        del query['modified_usage']

if not allow_empty_search and not query:
    LOG('CPSDefault.search', DEBUG, 'No query provided => no answers')
    return []

# scope of search
if folder_prefix:
    if not query.has_key('path'):
        portal_path = '/' + catalog.getPhysicalPath()[1] + '/'
        query['path'] =  portal_path + folder_prefix

    if query.has_key('search_relative_path'):
        current_depth = len(folder_prefix.split('/')) + 1
        query['relative_path_depth'] = current_depth

if query.has_key('folder_prefix'):
    del query['folder_prefix']

if query.has_key('search_relative_path'):
    del query['search_relative_path']

# use filter set to remove objects inside 'portal_*' or named '.foo'
query['cps_filter_sets'] = {'query': ['searchable'],
                            'operator': 'and'}
if default_languages:
    query['cps_filter_sets']['query'].append('default_languages')
if hide_folder:
    query['cps_filter_sets']['query'].append('leaves')

# title search
if query.has_key('Title'):
    # we search on the ZCTextIndex,
    # Title index is a FieldIndex only used for sorting
    query['ZCTitle'] = query['Title']
    del query['Title']

# start/end search
if start_date and not query.has_key('start'):
    query['start'] = {'query': start_date,
                      'range': 'min'}
if end_date and not query.has_key('end'):
    query['end'] = {'query': end_date,
                    'range': 'max'}
# sorting
if sort_by:
    if sort_by in ('title', 'date'):
        sort_by = sort_by.capitalize()  # for compatibility
    elif sort_by == 'status':
        sort_by = 'review_state'
    elif sort_by == 'author':
        sort_by = 'Creator'
    query['sort-on'] = sort_by

if direction:
    if not query.has_key('sort-order'):
        if direction.startswith('desc'):
            query['sort-order'] = 'reverse'
    else:
        if direction.startswith('asc') and query['sort-order'] == 'reverse':
            del query['sort-order']
        
if sort_limit and not query.has_key('sort-limit'):
    query['sort-limit'] = sort_limit

LOG('CPSDefault.search', DEBUG, 'start catalog search for %s' % query)
try:
    brains = catalog(**query)
    LOG('CPSDefault.search', DEBUG, 'found %s items' % (len(brains)))
except ParseErrors:
    LOG('CPSDefault.search', INFO, 'got an exception during search %s' % query)
    return []
return brains
