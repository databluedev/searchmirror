# project/appname/cqlmodels.py 

# from django.conf import settings

# import uuid
# from cassandra.cqlengine import columns
# from cassandra.cqlengine import connection
# from cassandra.cqlengine.models import Model
# from cassandra.cqlengine.management import sync_table
# from cassandra.auth import PlainTextAuthProvider

# CASSANDRA_USERNAME = ""
# CASSANDRA_PASSWORD = ""
# CASSANDRA_KEYSPACES = ""  
# CASSANDRA_HOST = ""
# CASSANDRA_PORT = 90

# auth_provider = PlainTextAuthProvider(username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD)
# connection.setup([CASSANDRA_HOST], CASSANDRA_KEYSPACES, auth_provider=auth_provider, protocol_version=4, port=CASSANDRA_PORT)
 
# class Cqlresult(Model): 
#     raw_id = columns.UUID(primary_key=True, default=uuid.uuid4) 
#     remote_keyword_id = columns.Integer(primary_key=True, clustering_order="ASC")
#     date = columns.Text()  
#     keyword_slug = columns.Text()  
#     raw_data = columns.Text()  
#     created_date = columns.Text()
#     modified_date = columns.Text() 