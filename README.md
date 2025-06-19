# arches-afs-oc-etl
ETL to prepare data for an Arches for Science demonstration

This repo has some Python code used for "Extract Transform Load" (ETL) processes to move legacy reference and sample collection item data into an Arches instance. The Arches instance needs to have the "Arches for Science" (https://github.com/archesproject/arches-for-science) application and package installed. For development purposes, one can deploy this "Arches for Science" ready instance using this Docker-based (https://github.com/opencontext/arches-via-docker/tree/local-afs-dev-2-x-demo) approach.

## Background

We're using the Arches relational views feature (see documentation: https://arches.readthedocs.io/en/7.6/developing/reference/import-export/#sql-import) as the main route for the ETL. Python scripts take the legacy dataset and reshape these data into multiple "staging" tables stored in a "staging" schema on the Arches PostgreSQL database. Certain UUIDs are read or generated to make it easier to trace-back the provenance of data through the ETL process. The "staging" data tables are also saved externally as CSV files to facilitate debugging and replication. 

The Python scripts read configurations to understand how to transform raw data into data for the staging tables. These configurations are also used to generate SQL statements used to move data from the staging tables in the "staging" schema into various tables defined by the Arches relational views. These configurations and the code that reads these configurations should in theory be a useful basis for other Arches ETL needs beyond the "Arches for Science" application and package.


## How To

This is not intended to be a fully polished ETL pipeline into Arches. It's mainly an ad hoc assemblage of some handy scripts to help with ETL projects in a *hopefully* more reproducible manner.

### Created a staging schema in your Arches AfS Demo PostgreSQL database (Arches database PostgreSQL connection)

```sql

CREATE SCHEMA IF NOT EXISTS staging;

```


### In a Python shell, populate the staging schema with data ready loading into Arches

```python

from arches_afs import etl
# Prepare the staging tables, load them into the staging table, save them
# do the data directory.
dfs = etl.prepare_all_transformed_data()
# Prepare the SQL statements and save them as a file in the data directory.
sqls = etl.prepare_all_sql_inserts()

```


### Execute the SQL statements to load into Arches

Execute the SQL statements in the `etl_sql.txt` file. The order of operations matters, so make sure you have
the inserts for resource instances run before you attempt to load tile data.


### Run Management Command

Execute the following management command to "publish" the newly ETL'd records:

```shell
# Do Migrations
docker exec -it arches python manage.py migrate afs
```


### NOTE: Why don't my Name Descriptors show up in Arches?

It seems there's a problem with the node alias (or something) with various resource model name descriptors in the AfS application / package. Using the Arches user-interface, navigate to the "functions" and update the descriptor functions for the name. You may have better luck with the alias `<Name_content>` than with the all lowercase `<name_content>`


### NOTE: Dump the database

Here's a quick way to dump the Arches-AfS-Demo PostgreSQL database:

```shell

# Make a database dump
docker exec -it arches bash -c "pg_dump -U postgres -h arches_db -F c -b afs_demo > '/arches_data/afs_demo.dump'"

```