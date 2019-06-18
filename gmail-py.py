import os, datetime, email
import re
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


def send_email():
    newEmail = EmailSMTP()
    server = newEmail.beginConnection()
    # Better UI
    # Need to add exception handling
    # Ability to switch smtp address based on users email
    # CC and BCC
    # Options to input html emails
    # formatting options
    # ability to upload one or more files
    # add a signature
    recipient = input("Whos it to?")

    while not is_email(recipient):
        recipient = input('Please enter a valid email address or press 1. to go back to the main menu\n')
        if recipient == '1':
            menu_select()
        else:
            continue

    subject = "Subject: " + input("What is the subject line? \n")+"\n"
    body = input("What is the text body? \n")
    emailText = subject + body
    newEmail.sendMail(server, recipient, emailText)
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
        menu_select()
    elif response == '2':
        menu_select()

def is_email(email):
    validAddress = re.compile(r'\b[a-zA-Z0-9\.\-\_]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}\b')
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
