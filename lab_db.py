import sqlite3
from flask import g

class Lab_DB:

    def __init__(self, db_path, app=None):
        '''
        http://flask.pocoo.org/docs/0.12/patterns/sqlite3/
        '''
        self.db_path = db_path
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.teardown_appcontext(self.close_connection)

    def close_connection(self, exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

    @property
    def con(self):
        '''
        https://docs.python.org/3/library/sqlite3.html#using-the-connection-as-a-context-manager
        
        with db.con as con:
            con.execute("insert into person(firstname) values (?)", ("Joe",))
        '''
        con = getattr(g, '_database', None)
        if con is None:
            con = g._database = sqlite3.connect(self.db_path)
            con.row_factory = sqlite3.Row # make it return namedtuple for each result
        return con
    
    def query(self, query, args=(), one=False):
        cur = self.con.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv




# 数据库使用样例 example db query
'''
user = db.query('select * from members where grade = ?',
                [the_username], one=True)
if user is None:
    print 'No such user'
else:
    print the_username, 'has the id', user['user_id']
    
'''

# 其它
'''    
注意：1. sqlite3自动commit
      2. 非查询语句下fetchall返回[]

参考： 
    1. https://stackoverflow.com/questions/4699605/sqlite3-saving-changes-without-commit-command-in-python
    2. https://stackoverflow.com/questions/36243538/python-sqlite3-how-often-do-i-have-to-commit/36244223#36244223
    3. http://www.sqlitetutorial.net/sqlite-transaction/
    4. https://stackoverflow.com/questions/9754913/clarification-of-java-sqlite-batch-and-auto-commit
    5. https://sqlite.org/lockingv3.html
'''