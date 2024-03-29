import sys
import psycopg2
import datetime
import config
import json
from gallery_dl import job
from gallery_dl import config as dlconfig
from gallery_dl.extractor.message import Message
from psycopg2.extras import RealDictCursor
from download import download_file, DownloaderException
from flag_check import check_for_flags
from proxy import get_proxy
from io import StringIO
from html.parser import HTMLParser
from os.path import join
from proxy import get_proxy

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def import_posts(key):
    conn = psycopg2.connect(
        host = config.database_host,
        dbname = config.database_dbname,
        user = config.database_user,
        password = config.database_password,
        cursor_factory = RealDictCursor
    )

    dlconfig.set(('output'), "mode", "null")
    dlconfig.set(('extractor', 'subscribestar'), "cookies", {
        "auth_token": key
    })
    dlconfig.set(('extractor', 'subscribestar'), "proxy", get_proxy())
    j = job.DataJob("https://subscribestar.adult/feed") 
    j.run()
    
    for message in j.data:
        try:
            if message[0] == Message.Directory:
                post = message[-1]

                file_directory = f"files/subscribestar/{post['author_name']}/{post['post_id']}"
                attachments_directory = f"attachments/subscribestar/{post['author_name']}/{post['post_id']}"
                
                cursor1 = conn.cursor()
                cursor1.execute("SELECT * FROM dnp WHERE id = %s AND service = 'subscribestar'", (post['author_name'],))
                bans = cursor1.fetchall()
                if len(bans) > 0:
                    continue
                
                check_for_flags(
                    'subscribestar',
                    post['author_name'],
                    str(post['post_id'])
                )

                cursor2 = conn.cursor()
                cursor2.execute("SELECT * FROM booru_posts WHERE id = %s AND service = 'subscribestar'", (str(post['post_id']),))
                existing_posts = cursor2.fetchall()
                if len(existing_posts) > 0:
                    continue
                
                stripped_content = strip_tags(post['content'])
                post_model = {
                    'id': str(post['post_id']),
                    '"user"': post['author_name'],
                    'service': 'subscribestar',
                    'title': (stripped_content[:60] + '..') if len(stripped_content) > 60 else stripped_content,
                    'content': post['content'],
                    'embed': {},
                    'shared_file': False,
                    'added': datetime.datetime.now(),
                    'published': post['date'],
                    'edited': None,
                    'file': {},
                    'attachments': []
                }

                for attachment in list(filter(lambda msg: post['post_id'] == msg[-1]['post_id'] and msg[0] == Message.Url, j.data)):
                    if (len(post_model['file'].keys()) == 0):
                        filename, _ = download_file(
                            join(config.download_path, file_directory),
                            attachment[-1]['url'],
                            name = attachment[-1]['filename'] + '.' + attachment[-1]['extension']
                        )
                        post_model['file']['name'] = attachment[-1]['filename'] + '.' + attachment[-1]['extension']
                        post_model['file']['path'] = f'/{file_directory}/{filename}'
                    else:
                        filename, _ = download_file(
                            join(config.download_path, attachments_directory),
                            attachment[-1]['url'],
                            name = attachment[-1]['filename'] + '.' + attachment[-1]['extension']
                        )
                        post_model['attachments'].append({
                            'name': attachment[-1]['filename'] + '.' + attachment[-1]['extension'],
                            'path': f'/{attachments_directory}/{filename}'
                        })
                
                post_model['embed'] = json.dumps(post_model['embed'])
                post_model['file'] = json.dumps(post_model['file'])
                for i in range(len(post_model['attachments'])):
                    post_model['attachments'][i] = json.dumps(post_model['attachments'][i])

                columns = post_model.keys()
                data = ['%s'] * len(post_model.values())
                data[-1] = '%s::jsonb[]' # attachments
                query = "INSERT INTO booru_posts ({fields}) VALUES ({values})".format(
                    fields = ','.join(columns),
                    values = ','.join(data)
                )
                cursor3 = conn.cursor()
                cursor3.execute(query, list(post_model.values()))
                conn.commit()
        except DownloaderException:
            continue
    
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        import_posts(sys.argv[1])
    else:
        print('Argument required - Login token')