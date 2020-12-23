from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
import config

pool = ThreadedConnectionPool(1, 100,
    host = config.database_host,
    dbname = config.database_dbname,
    user = config.database_user,
    password = config.database_password,
    cursor_factory = RealDictCursor
)