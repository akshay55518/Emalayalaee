from urllib.parse import urlencode
from django.db import connection
from math import ceil

# Fetch paginated data from the database
def fetch_paginated_data(query, params, page, page_size, request):
    offset = (page - 1) * page_size
    base_url = request.build_absolute_uri(request.path) if request else ""
    print(base_url)
    
    with connection.cursor() as cursor:
        # Count query
        count_query = f"SELECT COUNT(*) FROM ({query}) as sub"
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()[0]

        # Paginated query
        paginated_query = f"{query} LIMIT %s OFFSET %s"
        cursor.execute(paginated_query, params + [page_size, offset])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

    results = [dict(zip(columns, row)) for row in rows]
    return total_records, results, base_url

# Build pagination structure
def build_pagination(base_url, page, page_size, total_records, window=3, edge=2):
    """
    Build pagination with leading/trailing pages and ellipsis (…).
    window = number of pages around current
    edge = number of always-visible first/last pages
    """
    total_pages = ceil(total_records / page_size) if page_size > 0 else 1
    if total_pages < 1:
        total_pages = 1

    def build_url(p):
        return f"{base_url}?{urlencode({'page[number]': p, 'page[size]': page_size})}"
        # return f"{base_url}?(urelencode({page[number]={p}&page[size]={page_size}}))"

    # Pages near the current page
    start_page = max(1, page - window)
    end_page = min(total_pages, page + window)
    page_range = list(range(start_page, end_page + 1))

    # Ensure first & last edge pages
    leading = list(range(1, edge + 1))
    trailing = list(range(total_pages - edge + 1, total_pages + 1))

    # Merge & avoid duplicates
    pages = sorted(set(leading + page_range + trailing))
    
    # Insert ellipsis indicators
    display_pages = []
    last = None
    for p in pages:
        if last and p - last > 1:
            display_pages.append("…")
        display_pages.append(p)
        last = p

    return {
        "total_pages": total_pages,
        "current_page": page,
        "pages": [
            {"page": p, "url": build_url(p), "is_active": p == page} if p != "…" else {"page": "…"} 
            for p in display_pages
        ],
        "first_page": build_url(1) if page > 1 else None,
        "previous_page": build_url(page - 1) if page > 1 else None,
        "next_page": build_url(page + 1) if page < total_pages else None,
        "last_page": build_url(total_pages) if page < total_pages else None,
    }
    
