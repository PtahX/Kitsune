from shutil import rmtree
from os.path import join
from psycopg2.extras import RealDictCursor
import psycopg2
import config
def check_for_flags(service, user, post):
    conn = psycopg2.connect(
        host = config.database_host,
        dbname = config.database_dbname,
        user = config.database_user,
        password = config.database_password,
        cursor_factory = RealDictCursor
    )
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM booru_flags WHERE service = %s AND "user" = %s AND id = %s', (service, user, post))
    existing_flags = cursor.fetchall()
    if len(existing_flags) == 0:
        return
    
    cursor.execute('DELETE FROM booru_flags WHERE service = %s AND "user" = %s AND id = %s', (service, user, post))
    cursor.execute('DELETE FROM booru_posts WHERE service = %s AND "user" = %s AND id = %s', (service, user, post))
    conn.commit()
    rmtree(join(
        config.download_path,
        'attachments',
        '' if service == 'patreon' else service,
        user,
        post
    ), ignore_errors=True)
    rmtree(join(
        config.download_path,
        'files',
        '' if service == 'patreon' else service,
        user,
        post
    ), ignore_errors=True)
    conn.close()