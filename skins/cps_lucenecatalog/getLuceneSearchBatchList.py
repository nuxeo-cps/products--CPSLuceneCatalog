##parameters=items=[], columns=1, items_per_page=10, zoom=0, max_items=100
# $Id: getBatchList.py 6281 2004-06-25 13:45:03Z dwyart $
"""
Given the desired number of colums, constructs a list of batches to render
as much columns as necessary within a single macro.
As well, return the page results link to display straight for the navigation
"""

from math import ceil
from ZTUtils import Batch

#
# First constructing the batch
#

if len(items):
    len_items = items[0].out_of
else:
    len_items = 0

# desperately empty, no need to go further
if not len_items:
    return [], {}, []

if max_items and max_items < len_items:
    items = items[:max_items]
    len_batch = max_items
else:
    len_batch = len_items

b_start = int(context.REQUEST.get('b_start', 0))
b_size = int(context.REQUEST.get('b_size', 10))

# extract the n first items in a zoomed list
zoomed = []
if not b_start and zoom:
    zoom = int(zoom)
    zoomed = Batch(items[:zoom], zoom, 0)
    # deal with items left
    items = items[zoom:]

items_per_page = float(b_size)
size = int(ceil(float(items_per_page) / columns))

#b1 = Batch(items, 0, len(items), orphan=0)
b1 = items
batches = [b1]

b_next = b1
for c in range(columns - 1):
    if b_next.next:
        b_next = b_next.next
        batches.append(b_next)

#
# Now the page results parameters
#

# Calculate the number of pages
#raise str(len_batch)
#raise str(ceil(len_batch / items_per_page))
nb_pages = int(ceil(float(len_items) / float(size)))

# no more advanced arithmetics
items_per_page = int(items_per_page)

# Test if we are on the last page
limit = b_start + items_per_page
if  limit > len_batch:
    limit = len_batch

batch_info = {'nb_pages': nb_pages,
              'start': b_start,
              'limit': limit,
              'length': len_items,
              'previous': None,
              'next': None,
              }

# for the nb of items
j = 0
# for the current position in the search
current = [0, 1]
# list of b_start values
pages = []

# Loop over the number of pages and construct the page link
for i in range(nb_pages):
    pages.append(j)
    if b_start == j:
        current = [i + 1, j]
    j += items_per_page

# list of b_start to other pages
batch_info['pages'] = pages

# if we are not at the beginning of the file
if current[0] > 1:
    batch_info['previous'] = current[1] - items_per_page

# Adding the next link if we are not at the end of the list
if current[0] != nb_pages:
    batch_info['next'] = current[1] + items_per_page

return batches, batch_info, zoomed
