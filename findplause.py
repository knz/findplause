# Copyright (c) 2018, Raphael ‘kena’ Poss
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from urllib import parse as urlparse
from http import server
import time
import re
import os
from slackclient import SlackClient
from datetime import datetime, timezone, timedelta, date

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write(intro_page.encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))
        fields = urlparse.parse_qs(post_data)
        args = {}
        print("WAA", fields)
        for f in ['token', 'until_date', 'from_date', 'reaction']:
            bf = bytes(f, 'utf-8')
            args[f] = ''.join((x.decode('utf-8') for x in fields.get(bf, b'')))
            
        print("WAA", args)
        self._set_response()
        page = header + gen_form(**args) + gen_response(**args) + footer
        self.wfile.write(page.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    url = 'http://%s:%s/' % (httpd.server_name, httpd.server_port)
    os.system('open %s' + url)
    print("\nURL: %s\n" % url)
  
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

header = '''
<!DOCTYPE html>
<html lang='en'>
<head>
<title>Plause extractor</title>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">
<!--[if lt IE 9]>
  <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
  <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
<![endif]-->
</head>
<body>
<div class="container">
<h1>Plause extractor</h1>
'''

footer = '''</div></body></html>'''

def gen_form(token = '', reaction = 'plause', from_date=None, until_date=None):
    if from_date is None:
        from_date = date.today() - timedelta(7)
    if until_date is None:
        until_date = from_date + timedelta(7)

    return '''
<form method=POST action=''>
<div class=row>
<label for=token>Slack token:</label>
<input type=text name=token style='width:100%%' value='%(token)s'>
<p class='alert alert-info'>The slack token must have permissions <strong>reactions:read</strong>, <strong>users:read</strong> and <strong>search:read</strong></p>
</div>

<div class=row>
<label for=from_date>Start date:</label>
<input type=date name=from_date value='%(from_date)s'>

<label for=until_date>End date:</label>
<input type=date name=until_date value='%(until_date)s'>
</div>

<div class=row>
<label for=plause>Search reaction:</label>
<input type=text name=reaction value='%(reaction)s'>
</div>

<div class=row>
<input class='btn btn-lg btn-primary' type=submit name=submit value=Search>
</div>
</form>
''' % locals()

intro_page = header + gen_form() + footer

re_user = re.compile(r'<@(U[A-Z0-9]*)>')

def replace_users(slack_client, text):
    return re_user.sub(lambda m:find_user(slack_client, m), text)

user_cache = {}

def find_user(slack_client, matchobj):
    global user_cache
    user_id = matchobj.group(1)

    username = user_cache.get(user_id, None)
    if username is None:
        m = slack_client.api_call('users.info', user = user_id)
        print("WYY", m)
        if m.get('ok', None) != True:
            username = user_id
        else:
            username = m['user']['name']
            user_cache[user_id] = username
    return '@' + username

def gen_response(token = '', reaction='plause', from_date=None, until_date=None):
    slack_client = SlackClient(token)

    if from_date is None:
        from_date = date.today() - timedelta(7)
    elif type(from_date) == type(''):
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    from_date = from_date - timedelta(1)
    if until_date is None:
        until_date = from_date + timedelta(7)
    elif type(until_date) == type(''):
        until_date = datetime.strptime(until_date, '%Y-%m-%d').date()
    until_date = until_date + timedelta(1)
    
    
    query='has::%s: before:%s after:%s' % (reaction, until_date, from_date)

    lines = []
    finish = lambda:'<hr/>' + ''.join(('<div class=row>%s</div>' % x for x in lines))
    try:
        m = slack_client.api_call('search.messages', query=query, sort='timestamp', sort_dir='asc', count=100)
        print("WOO", m)
        if m.get('ok', None) != True:
            lines.append("""<p class='alert alert-danger'>Error: %r</p>""" % m)
            return finish()
    except Exception(e):
        lines.append("""<p class='alert alert-danger'>Error: %r</p>""" % e)
        return finish()

    num_messages = m['messages']['total']
    if num_messages > 100:
        lines.append("""<p class='alert alert-danger'>Too many results (%d). Use a smaller date range.</p>""" % num_messages)
        return finish()

    rows = []
    matches = m['messages']['matches']
    for msg in matches:
        print("WAA", msg)
        # lines.append("WAA %r" % msg)
        author = msg['username']
        text = msg['text']
        text = replace_users(slack_client, text)
        channel_name = msg['channel']['name']
        channel = msg['channel']['id']
        ts = msg['ts']
        permalink = msg['permalink']
        msg_date = datetime.fromtimestamp(float(ts), timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        # print("[%s] #%s @%s: %s" % (msg_date, channel_name, author, text))
        # print("\turl:", msg['permalink'])
        # Retrieve specific reactions
        n = slack_client.api_call('reactions.get', channel = channel, timestamp = ts)
        if n.get('ok', None) != True:
            lines.append("<p class='alter alter-warning'>Error retrieving reactions: %r</p>" % n)
            continue
        else:
            reactions = n['message']['reactions']
            print("WUU", reactions)
            for r in reactions:
                if r['name'] != reaction:
                    continue
                rows.append('''<tr><td>%d</td><td><a href=%s>%s</a></td><td>#%s</td><td>[@%s] %s</td></tr>''' %
                            (r['count'], permalink, msg_date, channel_name, author, text))
                
                # print("\t:%s: %d" % (r['name'], r['count']))
    if len(rows) > 0:
        lines.append("<h1>Results</h1>")
        lines.append("""
<div class=table><table class='table table-hover'>
<thead><tr><th>Count</th><th>When</td><th>Where</th><th>Message</th></tr></thead>
<tbody>%s</tbody></table></div>""" % ''.join(rows))
    else:
        lines.append("<h1>No results</h1>")
    

    return finish()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
