# -*- coding: utf-8 -*-
import smtplib
import time

from email.header import Header
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr, make_msgid

# python 2
string_types = basestring,
text_type = unicode
message_policy = None


def sanitize_address(addr, encoding='utf-8'):

    name, addr = parseaddr(addr)

    name = Header(name, encoding).encode()
    addr.encode('ascii')
    return formataddr((name, addr))


def sanitize_addresses(addresses, encoding='utf-8'):
    return map(lambda e: sanitize_address(e, encoding), addresses)


class Connection(object):

    def __init__(self, mail):
        self.mail = mail

    def __enter__(self):
        if self.mail.suppress:
            self.host = None
        else:
            self.host = self.configure_host()

        self.num_emails = 0

        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.host:
            self.host.quit()

    def configure_host(self):
        if self.mail.use_ssl:
            host = smtplib.SMTP_SSL(self.mail.server, self.mail.port)
        else:
            host = smtplib.SMTP(self.mail.server, self.mail.port)

        host.set_debuglevel(int(self.mail.debug))

        if self.mail.user_tls:
            host.starttls()
        if self.mail.username and self.mail.password:
            host.login(self.mail.username, self.mail.password)

        return host

    def send(self, message, envelope_from=None):

        if message.has_bad_headers():
            raise BasHeaderError

        if message.date is None:
            message.date = time.time()

        if self.host:
            self.host.sendmail(
                sanitize_address(envelope_from or message.sender),
                list(sanitize_addresses(message.send_to)),
                message.as_string(),
                message.mail_options,
                message.rcpt_options)

    def send_message(self, *args, **kwargs):
        self.send(Message(*args, **kwargs))


class BasHeaderError(Exception):
    pass


class Message(object):

    def __init__(self, subject='',
                 recipients=None,
                 body=None,
                 html=None,
                 alts=None,
                 sender=None,
                 cc=None,
                 bcc=None,
                 reply_to=None,
                 date=None,
                 charset=None,
                 extra_headers=None,
                 mail_options=None,
                 rcpt_options=None):

            sender = sender
            if isinstance(sender, tuple):
                sender = '%s <%s>' % sender

            self.subject = subject
            self.recipients = recipients or []
            self.body = body
            self.html = html
            self.sender = sender
            self.reply_to = reply_to
            self.cc = cc or []
            self.bcc = bcc or []
            self.alts = dict(alts or {})
            self.charset = charset
            self.date = date
            self.extra_headers = extra_headers
            self.msgId = make_msgid()
            self.mail_options = mail_options or []
            self.rcpt_options = rcpt_options or []

    @property
    def send_to(self):
        pass


if __name__ == '__main__':
    addr = sanitize_address('chinabingwei@163.com')
    print addr
