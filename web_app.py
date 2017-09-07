from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify
from flask import abort
from flask import after_this_request
from flask import g

# 增加登录验证: https://flask-login.readthedocs.io/en/latest/  
from flask_login import LoginManager
from flask_login import login_required
from flask_login import login_user
from flask_login import UserMixin

# 增加websocket
from flask_sockets import Sockets
from gevent.queue import Queue
import gevent

from jinja2 import Template
from my_mail import sendmail
from lab_db import Lab_DB
import sqlite3
import datetime
import settings


app = Flask(__name__)
app.secret_key = settings.KEY
app.date = None

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

db = Lab_DB(db_path=settings.DATABASE)
db.init_app(app)

sockets = Sockets(app) # plus socket
Q = Queue()

infos = settings.INFOS
zhuguan = settings.ZHUGUAN
table = settings.EMAIL_TABLE
template = Template(table)
user_db = settings.ADMINS
# 初始status为全员都到:(主管统一签到)
status = {} 
# 初始status为全员都未到且原因未知:(自己签到) # 不方便使用defaultdict
status = {name: '原因'  for i in infos for name in i['names']}

# ----------------- 用户及登录 (----------------- #
class User(UserMixin):
    '''
    https://flask-login.readthedocs.io/en/latest/#your-user-class
    http://docs.jinkan.org/docs/flask-login/_modules/flask/ext/login.html#UserMixin
    UserMixin包含：
        def get_id(self):
            return self.id
        def is_active(self):
            return True
        def is_anonymous(self):
            return False
        def is_authenticated(self):
            return True
    '''
    def __init__(self, email):
        self.id = email
        
    @classmethod
    def get(cls, user_id):
        if user_id in user_db:
            return cls(user_id)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/login", methods=["GET", "POST"])
def login():
    '''
    https://stackoverflow.com/questions/20766291/flask-login-not-redirecting-to-previous-page
    '''
    error = False
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user_password = user_db.get(email)
        
        if user_password and user_password == password:
            user = User(email)
            login_user(user, remember=True)
            next = request.args.get('next')
            return redirect(next or '/') # next if next else '/'
        else:
            error = True
            
    return render_template('login.html', error=error)
# ----------------- 用户及登录 )----------------- #

# ----------------- 主页面 (----------------- #
@app.route('/', methods=['GET'])
def kaoqin_helper():
    '''
    html样式模板： http://materializecss.com/getting-started.html
    '''
    
    # http://flask.pocoo.org/docs/0.12/api/#flask.make_response 等价
    @after_this_request
    def add_header(response):
        response.headers['X'] = 'haha'
        expires = datetime.datetime.now() + datetime.timedelta(days=365)
        response.set_cookie("some_cookie", 'some_value', expires=expires)
        return response
    # request.cookies.get("some_cookie")   
    
    # https://stackoverflow.com/questions/3759981/get-ip-address-of-visitors
    origin = request.headers.get('X-Forwarded-For', request.remote_addr)
    print(origin, '访问 - ', datetime.datetime.now())
    return render_template('index.html', infos=infos, zhuguan=zhuguan, status=status)

@app.route('/', methods=['POST'])
@login_required
def kaoqin_helper_send():

    def title():
        today = datetime.datetime.today()
        title = settings.TITLE.format(today.year, today.month, today.day)
        return title

    # 如果已经发送过则返回错误
    if db.query(
        'select date from history where date = ? and name = ? and status = ?',
        [datetime.date.today(), zhuguan, 'send']
    ):
        # abort(403)
        return 'You have already send today\'s email!'

    # username = request.form['username']
    print(request.form.getlist('at_lab'))
    person_at_lab = request.form.getlist('at_lab')
    
    # 也可不用处理表单, 信息基本都在status中了。
    lines = []
    sep = '<br/>'
    for i in infos:
        line = ['', '']
        for name in i['names']:
            if name in person_at_lab:
                line[0] += name + sep
                insert_history(name, '已经到达') # 记录历史
            else:
                if status.get(name) and status[name] != '原因':
                    insert_history(name, status[name])
                    line[1] += ''.join([name, '(', status[name], ')', sep])
                else:
                    insert_history(name, '未知原因') # 记录历史
                    line[1] += name + sep
        lines.append([i['header'], *line])
    
    body = template.render(lines=lines, zhuguan=zhuguan)

    # sendmail(title=title(), body=body, test=True)
    try:
        sendmail(title=title(), body=body, test=True)
    except Exception as e:
        print(e)
    else:
        print('send ok')

    insert_history(zhuguan, 'send')  # 记录历史
    status.clear() # 清空当前状态

    # 查询成员的sql语句, 仅为样例，无实际用途
    # global infos
    # for i in infos:
        # persons = db.query('select name from member where grade = ?', [i['header']])
        # i['names'] = [p['name'] for p in persons]
        # print(i['names'])
        
    return render_template('index.html', infos=infos, zhuguan=zhuguan, status=status)
# ----------------- 主页面 )----------------- #

def insert_history(name, status):
    with db.con as con:
        con.execute(
            "insert into history (name, date, status) values (?, ?, ?)",
            [name, datetime.date.today(), status])
    
# ----------------- ajax数据提交 (----------------- #
@app.route('/change_zhuguan', methods=['POST'])
@login_required
def change_zhuguan():
    global zhuguan
    if request.method == 'POST':
        new = request.form.get('zhuguan').strip()
        if new:
            zhuguan = new
    return redirect('/')

@app.route('/report/<name>', methods=['POST'])
# @login_required  # 放开报告权限
def report(name):
    reason = request.args.get('reason', None)
    if reason:
        if reason == '到达':
            status.pop(name)
        else:
            status[name] = reason
            #
        data = {'name': name, 'reason': reason}
        Q.put(data)
        origin = request.headers.get('X-Forwarded-For', request.remote_addr)
        app.logger.info(' Time: {0}\n IP: {1}\n Data: {2}'.format(datetime.datetime.now(), origin, data))
            #
        # insert_history(name, reason) # 记录历史 # 不能这么记录
        print('all status ->', status)
    return jsonify(success=True)
    
# ----------------- ajax数据提交 )----------------- #


# ----------------- 清空当前状态 (----------------- #
@app.route('/clear', methods=['GET'])
@login_required
def clear_status():
    global status
    status.clear()
    Q.put({'clear': True})
    return redirect('/')
# ----------------- 清空当前状态 )----------------- #

# ----------------- 提供模板上下文 (----------------- #

@app.context_processor
def template_extras():
    '''
    context_processor:
        上下文处理的装饰器，返回的字典中的键可以在上下文中使用
    '''
    return {'reasons': settings.REASONS}
# ----------------- 提供模板上下文 )----------------- #


# ----------------- websocket 通知状态 (----------------- #
class NotifyBackend():
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        '''
        queue.Queue?
        '''
        self.clients = list()


    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        self.clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            self.clients.remove(client)

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        # it also fits : "for data in Q: "
        # because: https://github.com/gevent/gevent/blob/master/src/gevent/queue.py#L351
        import json
        # 1. oneway
        # for data in iter(lambda: json.dumps(Q.get()), None):
        # 2. another
        while True:
            data = json.dumps(Q.get())
            # explain: when Q.get block it will give control to greenlet controller
            # see: https://github.com/gevent/gevent/blob/master/src/gevent/queue.py#L268
            app.logger.debug(u'Sending message: {}'.format(data))
            # print(u'Sending message: {}'.format(data))
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        # http://www.gevent.org/intro.html
        gevent.spawn(self.run)

chats = NotifyBackend()
chats.start()
    
# https://github.com/heroku-examples/python-websockets-chat
# https://devcenter.heroku.com/articles/python-websockets
@sockets.route('/notify')
def echo_socket(ws):
    """Sends outgoing messages, via `NotifyBackend`."""
    chats.register(ws)

    while not ws.closed:
        # Context switch while `NotifyBackend.start` is running in the background.
        gevent.sleep(0.1)
# ----------------- websocket 通知状态 )----------------- #
    
if __name__ == '__main__':
    # 初始化数据库
    import os
    if not os.path.isfile(settings.DATABASE):
        """ 生成成员表的sql语句, 仅为样例，无实际用途
                    drop table if exists member;
                    create table member(
                        name,
                        grade
                    );
        """
        sql_script = """

                    drop table if exists history;
                    create table history(
                        name,
                        date DATE,
                        status
                    );
                    """
        with app.app_context():
            with db.con as con:
                con.executescript(sql_script)
                # 插入成员的sql语句, 仅为样例，无实际用途
                # members = []
                # for i in infos:
                    # for name in i['names']:
                        # members.append([name, i['header']])
                # con.executemany("insert into member (name, grade) values (?, ?)", members)
            con.commit()
    
    removedb = False
    try:
        # app.run(host='0.0.0.0', port=5000, debug=True)
        # use gevent otherwise the raw flask app can not handle just two requests
        # http://sergray.me/asynchony-in-the-flask.html
        import gevent.pywsgi
        from geventwebsocket.handler import WebSocketHandler # plus WebSocketHandler
        
        app.debug = False
        gevent_server = gevent.pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler) # plus last arg 
        gevent_server.serve_forever()  # instead of flask_app.run()
        
    finally:
        if removedb:
            print('debug: remove db')
            os.remove(settings.DATABASE)