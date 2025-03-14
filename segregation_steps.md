# Segregation Steps for Wildlife Compliance

# Step One: export wildlife compliance tables and reversion schema from ledger

Run pg_dump on the ledger database.

`pg_dump -U $LEDGER_USER_NAME -W --exclude-table='django_cron*' -t 'wildlifecompliance_*' -t 'django_*' -t 'taggit_*' -t 'auth_group' -t 'auth_permission' $LEDGER_DATABASE_NAME -h 127.0.0.1 > $EXPORT_DIRECTORY/wildlifecompliance_ledger_tables.sql`

`pg_dump --schema-only -U $LEDGER_DATABASE_NAME -W  -t 'reversion_*' -h 127.0.0.1 > $EXPORT_DIRECTORY/reversion_schema_wildlifecompliance_ledger_tables.sql`

# Step Two: create new wildlife compliance database

As a postgres admin user (`su postgres` then `psql`) create the new wildlife compliance database.

`CREATE DATABASE wildlifecompliance;`
`CREATE USER wildlifecompliance WITH PASSWORD '<password>';`
`GRANT ALL ON DATABASE wildlifecompliance to wildlifecompliance;`
`\c wildlifecompliance`
`create extension postgis;`
`GRANT ALL ON ALL TABLES IN SCHEMA public TO wildlifecompliance;`
`GRANT ALL ON SCHEMA public TO wildlifecompliance;`

# Step Three: import exported tables in to new wildlife compliance database

`psql "host=127.0.0.1 port=5432 dbname=wildlifecompliance user=wildlifecompliance password=<password> sslmode=require" < $EXPORT_DIRECTORY/wildlifecompliance_ledger_tables.sql`

`psql "host=127.0.0.1 port=5432 dbname=wildlifecompliance user=wildlifecompliance password=<password> sslmode=require" < $EXPORT_DIRECTORY/reversion_schema_wildlifecompliance_ledger_tables.sql`

# Step Four: Move django migration rows to temp table

While connected to the new wildlife compliance database, create a temporary copy of the django migrations table and delete all rows from the original django migrations table where the id is greater than 11.

`CREATE TABLE django_migrations_temp AS SELECT * from django_migrations;`

`DELETE FROM django_migrations WHERE id > 11;`

# Step Five: Update environment variable with new database url (and other variables)

Update the environment variables:

- DATABASE_URL=postgis://wildlifecompliance:<password>@<host_address>:25432/wildlifecompliance
- LEDGER_DATABASE_URL=postgis://<ledger_user_name>:<ledger_password>@<host_address>:25432/<ledger_database_name>
- PAYMENT_INTERFACE_SYSTEM_PROJECT_CODE=0566
- PAYMENT_INTERFACE_SYSTEM_ID=4
- WILDLIFECOMPLIANCE_EXTERNAL_URL='<wildlifecompliance_external_url>'

# Step 6: Run ledger_api_client migrations

Ensure environment is running python3.12 and python3.12-dev installed.

Install pip modules:

`pip install -r requirements.txt`

Run ledger_api_client migrations:

`python manage_wc.py migrate ledger_api_client`

# Step 7: Restore original django migrations

While connected to the new wildlife compliance database insert the rows from the temporary migrations table in to the django migrations table, then remove django_cron migrations.

`INSERT INTO django_migrations (id,app,name,applied) SELECT * FROM django_migrations_temp WHERE id > 11;`

`DELETE FROM django_migrations WHERE app = 'django_cron';`

# Step 8: Run all other migrations

`python manage_wc.py migrate`

# Step 9: Update fauna license category row

While connected to the new wildlife compliance database, run the following:

`UPDATE wildlifecompliance_licencecategory SET name='Fauna', short_name='Fauna', code='FAU' WHERE id=12;`