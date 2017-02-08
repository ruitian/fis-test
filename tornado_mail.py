# -*- coding: utf-8 -*-
import smtplib
import time

from email.header import Header
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, parseaddr, make_msgid

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


def sanitize_subject(subject, encoding='utf-8'):
    try:
        subject.encode('ascii')
    except UnicodeEncodeError:
        try:
            subject = Header(subject, encoding).encode()
        except UnicodeEncodeError:
            subject = Header(subject, 'utf-8').encode()
    return subject


def _has_newline(line):
    """Used by has_bad_header to check for \\r or \\n"""
    if line and ('\r' in line or '\n' in line):
        return True
    return False


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

        if self.mail.use_tls:
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
        return set(self.recipients) | set(self.cc or ()) | set(self.bcc or ())

    # @property
    # def html(self):
    #     return self.alts.get('html')
    #
    # @html.setter
    # def html(self, value):
    #     if value is None:
    #         self.alts.pop('html', None)
    #     else:
    #         self.alts['html'] = value

    def _mimetext(self, text, subtype='plain'):
        charset = self.charset or 'utf-8'
        return MIMEText(text, _subtype=subtype, _charset=charset)

    def _message(self):
        # 先不考虑带附件的情况
        # 下个版本将加入
        encoding = self.charset or 'utf-8'

        if not self.alts:
            msg = self._mimetext(self.body)
        else:
            msg = MIMEMultipart()
            alternative = MIMEMultipart('alternative')
            alternative.attach(self._mimetext(self.body, 'plain'))
            for mimetype, content in self.alts.items():
                alternative.attach(self._mimetext(content, mimetype))
            msg.attach(alternative)

        if self.subject:
            msg['Subject'] = sanitize_subject(self.subject, encoding)

        msg['From'] = sanitize_address(self.sender, encoding)
        msg['To'] = ', '.join(
            list(set(sanitize_addresses(self.recipients, encoding))))
        msg['Date'] = formatdate(self.date, localtime=True)
        msg['Message-ID'] = self.msgId

        if self.cc:
            msg['Cc'] = ', '.join(
                list(set(sanitize_addresses(self.cc, encoding))))

        if self.reply_to:
            msg['Reply-TO'] = sanitize_address(self.reply_to, encoding)

        if self.extra_headers:
            for k, v in self.extra_headers.items():
                msg['k'] = v

        return msg

    def as_string(self):
        return self._message().as_string()

    def has_bad_headers(self):
        headers = [self.sender, self.reply_to] + self.recipients
        for header in headers:
            if _has_newline(header):
                return True

        if self.subject:
            if _has_newline(self.subject):
                for linenum, line in enumerate(self.subject.split('\r\n')):
                    if not line:
                        return True
                    if linenum > 0 and line[0] not in '\t ':
                        return True
                    if _has_newline(line):
                        return True
                    if len(line.strip()) == 0:
                        return True
        return False

    def send(self, connection):
        connection.send(self)


class _MailMixin(object):

    def send(self, message, mail):
        with self.connect(mail) as connection:
            message.send(connection)

    def send_message(self, *args, **kwargs):
        self.send(Message(*args, **kwargs))

    def connect(self, email):
        return Connection(email)


class _Mail(_MailMixin):
    def __init__(self, server, username, password, port, use_tls, use_ssl,
                 default_sender, debug, max_emails, suppress,
                 ascii_attachments=False):
        self.server = server
        self.username = username
        self.password = password
        self.port = port
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.default_sender = default_sender
        self.debug = debug
        self.max_emails = max_emails
        self.suppress = suppress
        self.ascii_attachments = ascii_attachments


class Mail(_MailMixin):

    def __init__(self, config):
        self.init_app(config)

    def init_mail(self, config, debug=False, testing=False):
        return _Mail(
            config.get('MAIL_SERVER', '127.0.0.1'),
            config.get('MAIL_USERNAME'),
            config.get('MAIL_PASSWORD'),
            config.get('MAIL_PORT', 25),
            config.get('MAIL_USE_TLS', False),
            config.get('MAIL_USE_SSL', False),
            config.get('MAIL_DEFAULT_SENDER'),
            int(config.get('MAIL_DEBUG', debug)),
            config.get('MAIL_MAX_EMAILS'),
            config.get('MAIL_SUPPRESS_SEND', testing),
            config.get('MAIL_ASCII_ATTACHMENTS', False)
        )

    def init_app(self, config):
        state = self.init_mail(config, debug=True)
        return state


if __name__ == '__main__':
    config = dict(
        MAIL_SERVER='smtp.ym.163.com',
        MAIL_PORT=465,
        MAIL_USERNAME='ApeSo@finder.ren',
        MAIL_PASSWORD='723520wei',
        MAIL_USE_SSL=True,
        MAIL_DEFAULT_SENDER='ApeSo@finder.ren',
        MAIL_RECIPIENTS=['819799762@qq.com', 'dongbingwei@lsh123.com']
    )
    mail = Mail(config)
    _mail = mail.init_app(config)
    msg = Message(
        'Hello Tornado',
        sender=config.get('MAIL_DEFAULT_SENDER'),
        recipients=config.get('MAIL_RECIPIENTS')
    )
    mail.send(msg, _mail)
