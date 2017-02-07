# -*- coding: utf-8 -*-
import smtplib

from email.header import Header
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr

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


if __name__ == '__main__':
    addr = sanitize_address('chinabingwei@163.com')
    print addr
