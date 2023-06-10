#------------------------------------------------------------------------------
# Hands-On Lab: Data Engineering with Snowpark
# Script:       02_load_raw.py
# Author:       Jeremiah Hansen, Caleb Baechtold
# Last Updated: 1/9/2023
#------------------------------------------------------------------------------

import time
from snowflake.snowpark import Session
#import snowflake.snowpark.types as T
#import snowflake.snowpark.functions as F


POS_TABLES = ['country', 'franchise', 'location', 'menu', 'truck', 'order_header', 'order_detail']
CUSTOMER_TABLES = ['customer_loyalty']
TABLE_DICT = {
    "pos": {"schema": "RAW_POS", "tables": POS_TABLES},
    "customer": {"schema": "RAW_CUSTOMER", "tables": CUSTOMER_TABLES}
}

# SNOWFLAKE ADVANTAGE: Schema detection
# SNOWFLAKE ADVANTAGE: Data ingestion with COPY
# SNOWFLAKE ADVANTAGE: Snowflake Tables (not file-based)

def load_raw_table(session, tname=None, s3dir=None, year=None, schema=None):
    session.use_schema(schema)
    if year is None:
        location = f"@external.frostbyte_raw_stage/{s3dir}/{tname}"
    else:
        print(f'\tLoading year {year}')
        location = f"@external.frostbyte_raw_stage/{s3dir}/{tname}/year={year}"

    # we can infer schema using the parquet read option
    df = session.read.option("compression", "snappy") \
                            .parquet(location)
    df.copy_into_table(f"{tname}")

# SNOWFLAKE ADVANTAGE: Warehouse elasticity (dynamic scaling)

def load_all_raw_tables(session):
    _ = session.sql("ALTER WAREHOUSE HOL_WH SET WAREHOUSE_SIZE = XLARGE WAIT_FOR_COMPLETION = TRUE").collect()

    for s3dir, data in TABLE_DICT.items():
        tnames = data['tables']
        schema = data['schema']
        for tname in tnames:
            print(f"Loading {tname}")
            # Only load the first 3 years of data for the order tables at this point
            # We will load the 2022 data later in the lab
            if tname in ['order_header', 'order_detail']:
                for year in ['2019', '2020', '2021']:
                    load_raw_table(session, tname=tname, s3dir=s3dir, year=year, schema=schema)
            else:
                load_raw_table(session, tname=tname, s3dir=s3dir, schema=schema)

    _ = session.sql("ALTER WAREHOUSE HOL_WH SET WAREHOUSE_SIZE = XSMALL").collect()

def validate_raw_tables(session):
    # check column names from the inferred schema
    for tname in POS_TABLES:
        print(f"{tname}: \n\t{session.table(f'RAW_POS.{tname}').columns}\n")

    for tname in CUSTOMER_TABLES:
        print(f"{tname}: \n\t{session.table(f'RAW_CUSTOMER.{tname}').columns}\n")


# For local debugging
if __name__ == "__main__":
    # Add the utils package to our path and import the snowpark_utils function
    import os, sys
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

    from utils import snowpark_utils
    session = snowpark_utils.get_snowpark_session()

    load_all_raw_tables(session)
#    validate_raw_tables(session)

    session.close()
