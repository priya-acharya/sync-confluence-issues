import base64
import os
import smtplib
from subprocess import CalledProcessError, check_output, STDOUT

def create_email_message(from_user,to,subject,text):
    MESSAGE_FORMAT = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" # %(fromAddr,to,subject,text)
    message = MESSAGE_FORMAT%(from_user, to, subject, text) 
    return message

try:
    output = check_output(['venv\Scripts\pythonw.exe','src\maintain_arihant_defects.py'],stderr=STDOUT)
    returncode = 0
except CalledProcessError as e:
    output = e.output
    returncode = e.returncode

# print("return code is ",returncode,"output is",output)

if(returncode > 0 ):
    outlook_email = 'vishnupriya.nallanchakravarthula@jda.com'
    gmail_user = 'vpriya.nallan@gmail.com'
    gmail_pwd = base64.b64decode(os.environ['gcred'].encode('utf-8')).decode( 'utf-8' )
    # print('user',gmail_user,'password',gmail_pwd)

    smtpserver = smtplib.SMTP('smtp.gmail.com',587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(gmail_user, gmail_pwd)
    message = create_email_message(gmail_user,outlook_email,'confluence sync has failed',output)
    smtpserver.sendmail(gmail_user,outlook_email,message)
    smtpserver.close()

