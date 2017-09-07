import smtplib
from email.mime.text import MIMEText

from settings import HOST, SUBJECT, TO, FROM, PASSWORD, TO_TEACHER

template = """
    <table width="auto" border="0" cellspacing="0" cellpadding="8">
      <tr>
        <td bgcolor="#CECFAD" height="auto" style="font-size:20px">
            <b>{title}</b>
        </td>
      </tr>
      <tr>
        <td bgcolor="#EFEBDE" height="auto" style="font-size:20px">
            {body}
        </td>
      </tr>
    </table>"""
info_dict = {
    'title': 'X老师好，18年1月1日考勤情况如下：',
    'body': '<br>'.join([
        '1）研一:', 
        '&nbsp;'*4 + '准备考试',
        '2）研二:',
        '&nbsp;'*4 + 'a到，b请假',
        '3）研三:',
        '&nbsp;'*4 + '都没到',
        '4）博士:',
        '&nbsp;'*4 + '都到',
    ]),
}


def sendmail(title, body, subject=None, test=True):
    info_dict.update({
        'title': title,
        'body': body,
    })
    msg = MIMEText(template.format(**info_dict),"html","utf-8")

    msg['Subject'] = subject or SUBJECT
    msg['From'] = FROM
    to_ = TO if test else TO_TEACHER
    msg['To'] = to_
    BODY = msg.as_string()
    try:
        server = smtplib.SMTP(host=HOST, port="25")
        server.starttls()
        server.login(FROM, PASSWORD)
        server.sendmail(FROM, [to_], BODY)
        server.quit()
        print("邮件发送成功！")
    except Exception as e:  
        print("失败："+str(e) )


if __name__ == "__main__":
    mysendmail()
