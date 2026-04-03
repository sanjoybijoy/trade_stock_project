from django.core.management.base import BaseCommand
import os
import subprocess
import paramiko
import time

# Before sync you should connect through ssh tunnel to pythonanywhere
# Run the following command in Command Prompt 
# ssh -L 3307:sanjoybijoy.mysql.pythonanywhere-services.com:3306 sanjoybijoy@ssh.pythonanywhere.com
class Command(BaseCommand):
    help = "Sync local database with live database"

    def handle(self, *args, **options):
        local_dump_file = 'local_dump.sql'
        ssh_host = 'ssh.pythonanywhere.com'
        ssh_user = 'sanjoybijoy'
        ssh_password = 'p089chandra'  # Replace with your actual SSH password
        local_port = 3307
        remote_host = 'sanjoybijoy.mysql.pythonanywhere-services.com'
        remote_port = 3306

        # Establish SSH Tunnel
        self.stdout.write("Establishing SSH tunnel...")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(ssh_host, username=ssh_user, password=ssh_password)

            tunnel = ssh_client.get_transport().open_channel(
                "direct-tcpip",
                (remote_host, remote_port),
                ("localhost", local_port),
            )

            self.stdout.write("Dumping local database excluding session table...")
            dump_cmd = (
                f"mysqldump -u root -pm4001chandra "
                f"--ignore-table=stockiq_01.django_session stockiq_01 > {local_dump_file}"
            )
            subprocess.call(dump_cmd, shell=True)

            self.stdout.write("Importing into live database...")
            import_cmd = (
                f"mysql -u sanjoybijoy -ppm4001chandra "
                f"-h 127.0.0.1 --port={local_port} sanjoybijoy$stockiq_01 < {local_dump_file}"
            )
            subprocess.call(import_cmd, shell=True)

        finally:
            # Clean up
            self.stdout.write("Cleaning up...")
            if os.path.exists(local_dump_file):
                os.remove(local_dump_file)
            if tunnel is not None:
                tunnel.close()
            ssh_client.close()
            self.stdout.write("Database sync completed.")
