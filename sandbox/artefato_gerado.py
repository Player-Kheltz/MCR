import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configurações de monitoramento
monitor_path = '/caminho/para/o/diretorio'  # Substitua pelo caminho do diretório que deseja monitorar

# Configurações de email
smtp_server = 'smtp.exemplo.com'
smtp_port = 587
smtp_username = 'seu_email@example.com'
smtp_password = 'sua_senha'
from_email = 'seu_email@example.com'
to_email = 'destinatario@example.com'

class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            self.send_email(f'Arquivo modificado: {event.src_path}')

    def on_created(self, event):
        if not event.is_directory:
            self.send_email(f'Novo arquivo criado: {event.src_path}')

    def on_deleted(self, event):
        if not event.is_directory:
            self.send_email(f'Arquivo deletado: {event.src_path}')

    def send_email(self, message):
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = 'Alteração no diretório monitorado'

        body = f"Ocorreu uma alteração no diretório {monitor_path}:\n\n{message}"
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            print("Email enviado com sucesso!")
        except Exception as e:
            print(f"Erro ao enviar email: {e}")

if __name__ == "__main__":
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=monitor_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()