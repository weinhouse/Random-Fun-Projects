import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr


class Sendgrid:
    ''' class using Sendgrid as relay. free account allows 2k messages per day
        Service uses common username and a unique password id for auth. add
        this password at initialization '''

    smtp_relay = "smtp.sendgrid.net"
    sendgrid_user = "apikey"


    def __init__(self, password, reply_to_name, reply_to):
        ''' Initialize password, reply name, and reply email. for example:
        sg = mailer.Sendgrid("<pw>", "L Weinhouse", "larry@weinhouse.com") '''
        self.password = password
        self.reply_to_name = reply_to_name
        self.reply_to = reply_to


    def a_message(self, subject, body, to):
        ''' arguments are:
        subject(string), message(string), ["recipiant1","recipiant2". .](list)
        '''

        user = self.sendgrid_user
        password = self.password
        reply_to_name = self.reply_to_name
        reply_to = self.reply_to

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((str(Header(reply_to_name, 'utf-8')), reply_to))
        msg['To'] = ', '.join(to)
        msg['Subject'] = subject
        msg['Reply-to'] = reply_to
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP_SSL(self.smtp_relay, 465)
            server.ehlo()
            server.login(user, password)
            server.sendmail(user, ', '.join(to), msg.as_string())
            server.close()
            return 'Email sent'
        except Exception as e:
            return "Something went wrong: {}".format(e)
