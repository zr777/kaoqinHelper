# email
# 请修改下面的信息
HOST = "smtp.mail.xxx"
SUBJECT = "每日考勤"
TO = "test_email@x.com"
TO_TEACHER = "teacher_email@x.com"
FROM = "your_email@x.com"
PASSWORD = "your_password"

# flask app
ADMINS = {'somebody@x.com': '123456'}  # 情况简单，对密码不做处理
KEY = '41f99e13ddd43sdda58635f325e4f4f2dfd05e0245' # 盐，请修改
DATABASE = './database.db'
ZHUGUAN = '伊尹（yīyǐn）'
TITLE = 'X老师好，<br/> {0}年{1}月{2}日考勤情况如下：'
REASONS = ['请假', '上课', '实习']
INFOS = [
    {    
        'header': '研一',
        'names': ['祖逖（tì）', '蔡邕（yōng）', '老聃（dān）', '孙思邈（miǎo）'],
        'badge_color': 'red',
        'icon': 'directions_run',
    },
    {
        'header': '研二',
        'names': ['妲（dá）己', '身毒（yuāndú）', '伊尹（yīyǐn）', '召（shào）公', '临洮（táo）'],
        'badge_color': 'orange',
        'icon': 'airline_seat_recline_normal',
    },
    {
        'header': '研三',
        'names': ['张骞（qiān）', '邗（hán）沟', '大宛（yuān）'],
        'badge_color': 'purple',
        'icon': 'airline_seat_individual_suite',
    },
    {
        'header': '博士',
        'names': [ '墨翟（dí）', '虞姬（yújī）'],
        'badge_color': 'green',
        'icon': 'airplanemode_active',
    },
]
EMAIL_TABLE = """
<table border="2" rules="cols" cellpadding="15">
    <tr>
        <th>年级</th>
        <th>已到实验室</th>
        <th>尚未到达</th>
    </tr>
    {% for line in lines %}
    <tr>
        <td>{{ line[0] }}</td>
        <td>{{ line[1] }}</td>
        <td>{{ line[2] }}</td>
    </tr>
    {% endfor %}
</table>
<p align="right">
    当前主管： {{zhuguan}}
</p>
"""
