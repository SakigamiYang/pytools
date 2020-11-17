# coding: utf-8
import mimetypes
import smtplib
import typing
from email import encoders
from email.mime import text, image, audio, base, multipart
from os.path import isfile, basename


class SMTPMailer:
    """SMTP mailer."""

    def __init__(self,
                 sender: str,
                 server: str,
                 port: int = 25,
                 user: typing.Optional[str] = None,
                 password: typing.Optional[str] = None,
                 is_html: bool = False) -> None:
        """
        Initializer.
        :param sender: sender email address, e.g. xxx@xxx.com
        :param server: smtp server
        :param port: smtp port, 25 by default
        :param user: username for login smtp server
        :param password: password for login smtp server
        :param is_html: True for sending HTML based email. False by default.
        """
        self._server = server
        self._port = port
        self._sender = sender
        self._is_html = is_html
        self._login_params = {'user': user, 'password': password} if user and password else None

    @staticmethod
    def _handle_attachments(mime_multipart: multipart.MIMEMultipart,
                            attachments: typing.Optional[typing.Iterable[str]]) -> None:
        """
        Add attachments to mail.
        :param mime_multipart: mime multipart content
        :param attachments: list of attachments
        """
        for attachment in attachments:
            if not isfile(attachment):
                continue

            filename = basename(attachment)
            # Guess the content type based on the file's extension.
            ctype, encoding = mimetypes.guess_type(attachment)
            if not ctype or encoding:
                # No guess could be made, or the file is encoded (compressed),
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)

            if maintype == 'text':
                with open(attachment) as fin:
                    msg = text.MIMEText(fin.read(), subtype)
            elif maintype == 'image':
                with open(attachment, mode='rb') as fin:
                    filename = basename(attachment)
                    msg = image.MIMEImage(fin.read(), subtype)
                    msg.add_header('Content-ID', filename)
            elif maintype == 'audio':
                with open(attachment, 'rb') as fin:
                    filename = basename(attachment)
                    msg = audio.MIMEAudio(fin.read(), subtype)
            else:
                with open(attachment, 'rb') as fin:
                    msg = base.MIMEBase(maintype, subtype)
                    msg.set_payload(fin.read())
                # Encode the payload using Base64
                encoders.encode_base64(msg)
            msg.add_header(
                'Content-Disposition', 'attachment',
                filename=filename,
            )

            mime_multipart.attach(msg)

    def sendmail(self,
                 recipients: typing.Union[str, typing.Iterable[str]],
                 subject: str = '',
                 body: str = '',
                 attachments: typing.Union[None, str, typing.Iterable[str]] = None,
                 cc: typing.Union[None, str, typing.Iterable[str]] = None,
                 bcc: typing.Union[None, str, typing.Iterable[str]] = None) \
            -> typing.Tuple[bool, typing.Optional[str]]:
        """
        Send mail.
        :param recipients: recipient or list of recipients
        :param subject: subject of mail
        :param body: body of mail
        :param attachments: attachment path or list of attachments (NOTE: MUST use absolute file path)
        :param cc: cc of list of cc
        :param bcc: bcc or list of bcc
        :return: (True, None) on success, otherwise (False, error message)
        """
        to_addrs = list()
        recipients = [recipients] if isinstance(recipients, str) else recipients
        cc = [cc] if cc and isinstance(cc, str) else None
        bcc = [bcc] if bcc and isinstance(bcc, str) else None
        attachments = [attachments] if attachments and isinstance(attachments, str) else None
        body = text.MIMEText(body, 'html' if self._is_html else 'plain', 'utf-8')

        mime_multipart = multipart.MIMEMultipart()
        mime_multipart['From'] = self._sender
        mime_multipart['To'] = ','.join(recipients)
        if cc:
            mime_multipart['Cc'] = ','.join(cc)
        if bcc:
            mime_multipart['Bcc'] = ','.join(bcc)
        mime_multipart['Subject'] = subject
        mime_multipart.preamble = 'Peace and Love!\n'
        mime_multipart.attach(body)
        self._handle_attachments(mime_multipart, attachments)
        composed = mime_multipart.as_string()

        to_addrs.extend(recipients)
        if cc:
            to_addrs.extend(cc)
        if bcc:
            to_addrs.extend(bcc)

        try:
            smtp = smtplib.SMTP(self._server, self._port)
            if self._login_params:
                smtp.login(**self._login_params)
            smtp.sendmail(self._sender, to_addrs, composed)
            smtp.quit()
            return True, None
        except smtplib.SMTPException as smtp_err:
            return False, str(smtp_err)
