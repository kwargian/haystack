import polars as pl
import logging

def search_configs(query_params, conn):
    if len(query_params) > 1:
        # duckdb FTS and operator
        query_slug = ' & '.join(query_params)
        post_filter_terms = [f"config ILIKE '%{query_param}%'" for query_param in query_params]
        post_filter = ' AND '.join(post_filter_terms)
        post_filter = f" AND ({post_filter})" # stick an AND on the front so it works with the WHERE clause in the query below
    else:
        query_slug = query_params[0]
        post_filter = f" AND config ILIKE '%{query_slug}%'"

    # on it's own, the duckDB FTS AND operator is not as strict as we want (it'll return documents that match any of the terms, 
    # not just documents that match all of the terms) so we'll use post-filtering with ILIKE to enforce MATCH ALL behavior
    query = f"""
    SELECT hostname,serial_number
    FROM (
      SELECT *, fts_main_devices.match_bm25(
        serial_number,
        '{query_slug}',
        fields := 'config'
      ) AS score
      FROM devices
    ) sq
    WHERE score IS NOT NULL
    {post_filter}
    ORDER BY score DESC;
    """
    logging.info(f"Query: {query}")

    df = conn.execute(query).pl()
    # Print each row with column padding
    if len(df) > 0:
        # Get max width for each column
        col_widths = {col: max(len(str(val)) for val in df[col]) for col in df.columns}
        col_widths = {col: max(col_widths[col], len(col)) for col in col_widths}  # Account for header length
        
        # Print header
        header = " | ".join(col.ljust(col_widths[col]) for col in df.columns)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in df.iter_rows():
            row_str = " | ".join(str(val).ljust(col_widths[col]) for col, val in zip(df.columns, row))
            print(row_str)
    else:
        print("No results found")