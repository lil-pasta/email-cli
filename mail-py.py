import os, datetime, email
import os.path
import re
from os.path import basename
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import smtplib
from imapclient import IMAPClient
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL") or input("Enter your email: ")
EMAIL_PASSWORD = os.getenv("E_PASSWORD") or input("Enter your password: ")
SMTP_ADDRESS = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
IMAP_ADDRESS = os.getenv("IMAP_ADDRESS")

class EmailSMTP(smtplib.SMTP):
    def beginConnection(self):
        server = smtplib.SMTP(SMTP_ADDRESS, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        return server

    def sendMail(self, server, recipient, emailText):
        server.sendmail(EMAIL_ADDRESS, recipient, emailText)
        server.quit()

class EmailIMAP(IMAPClient):
    def beginConnection(self):
        server = IMAPClient('imap.gmail.com',
                           ssl=True,
                           use_uid=True)

        server.login(EMAIL_ADDRESS,
                     EMAIL_PASSWORD)
        return server

    def getRecentUnread(self, server):
        d = datetime.datetime.today().strftime('%d-%b-%Y')
        server.select_folder('[Gmail]/All Mail')
        messages = server.search(['ON',
                                  d,
                                  'UNSEEN'])

        for msgid, data in server.fetch(messages, ['ENVELOPE']).items():
            envelope = data[b'ENVELOPE']
            print('id %d: "%s" received %s' % (msgid,
                                               envelope.subject.decode(),
                                               envelope.date))

    def getEmail(self, server, msgid):
        message_data = server.fetch(msgid, 'RFC822')
        raw_email = message_data[msgid][b'RFC822'].decode("UTF-8")
        email_message = email.message_from_string(raw_email)

        print('To: \t', email_message['To'])
        print('From: \t', email_message['From'])
        print('Subject:', email_message['Subject'])

        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                print('Body:\n', part.get_payload())

        server.logout()

def generate_message():
    toAddr, ccAddr, bccAddr = [], [], []

    newAddr = ''
    print('Type in an address then press enter.')
    print('Then type \'done\' and press enter once you are done add recipients')
    while newAddr != 'done':
        newAddr = input('>>>')
        if newAddr != 'done' and is_email(newAddr):
            toAddr.append(newAddr)
        elif newAddr != 'done' and not is_email(newAddr):
            print('Please enter a valid email or type \'done\'')

    newAddr = ''
    print('Type in an address to cc then press enter.')
    print('Then type \'done\' and press enter once you are done add recipients')
    while newAddr != 'done':
        newAddr = input('>>>')
        if newAddr != 'done' and is_email(newAddr):
            ccAddr.append(newAddr)
        elif newAddr != 'done' and not is_email(newAddr):
            print('Please enter a valid email or type \'done\'')

    newAddr = ''
    print('Type in an address to bcc then press enter.')
    print('Then type \'done\' and press enter once you are done add recipients')
    while newAddr != 'done':
        newAddr = input('>>>')
        if newAddr != 'done' and is_email(newAddr):
            bccAddr.append(newAddr)
        elif newAddr != 'done' and not is_email(newAddr):
            print('Please enter a valid email or type \'done\'')

    subject = input("What is the subject line? \n")+"\n"
    body = input("What is the body of the text \n")
    emailMsg = MIMEMultipart()
    emailMsg['From'] = EMAIL_ADDRESS
    emailMsg['To'] = ", ".join(toAddr)
    emailMsg['CC'] = ", ".join(ccAddr)
    emailMsg['Subject'] = subject
    emailMsg.attach(MIMEText(body, 'plain'))

    toaddrs = toAddr + ccAddr + bccAddr

    payload = [emailMsg, toaddrs]
    return payload

def add_attachment():
    # make this function better.
    f = input('What file would you like to attach? If none type \'none\' to continue\n>>>')
    print(basename(f))
    if f != 'none':
        try:
           with open(f, 'rb') as fi:
               attachment = MIMEBase('fi', 'octet-stream')
               attachment.set_payload(fi.read())
        except Exception as e:
            print(e)
            print('No file attached but im sending your email anyways' +
                  'should probably come up with something better than this rude ass response')
            return
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition',
                        'attachment; filename="%s"' % basename(f))
        return attachment
    elif f == 'none':
        return


def send_email():
    newEmail = EmailSMTP()
    server = newEmail.beginConnection()
    # Better UI
    # Need to add exception handling
    # Ability to switch smtp address based on users email
    # Options to input html emails
    # formatting options
    # ability to upload one or more files
    # add a signature

    msg = generate_message()
    emailMsg = msg[0]
    print('do you have any attachments? Please enter yes or no')
    if input('>>>') == 'yes':
        attachment = add_attachment()
        emailMsg.attach(attachment)

    toaddrs = msg[1]
    newEmail.sendMail(server, toaddrs, emailMsg.as_string())
    menu_select()

def view_email():
    # Better UI
    # Support attachments
    # Exception handling
    # Ability to delete and respond to emails
    # show cc and bcc
    # html body support (smarter parsing of email body)
    # instead of showing just unread show a paginated list of emails and mark read/unread/starred and important
    inbox = EmailIMAP(IMAP_ADDRESS)
    server = inbox.beginConnection()
    inbox.getRecentUnread(server)
    print('Would you like to:\n1. Open an unread email')
    print('2. Return to main menu')
    response = input('>>>')
    if response == '1':
        msgid = int(input('Whats the UID of the email you wish to read?\n>>>'))
        inbox.getEmail(server, msgid)
        input('Hit enter when you\'re ready.')
        view_email()
    elif response == '2':
        menu_select()

def is_email(email):
    validAddress = re.compile(r'^[a-zA-Z0-9\.\-\_]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$')
    if validAddress.match(email):
        return True
    else:
        return False

def menu_select():
    print("Select an option:")
    print("1. Send an Email")
    print("2. View emails")
    print("3. Exit")
    choice = input(">>>")
    menu_item[choice]()

menu_item = {
    '1': send_email,
    '2': view_email,
    '3': exit
}

if __name__ == "__main__":
    menu_select()
