from django.core.management.base import BaseCommand
import os
import subprocess
import paramiko

# Before sync you should connect through ssh tunnel to pythonanywhere
# Run the following command in Command Prompt 
# ssh -L 3307:sanjoybijoy.mysql.pythonanywhere-services.com:3306 sanjoybijoy@ssh.pythonanywhere.com
# Uses:
# To sync live-to-local: python manage.py sync_databases --direction=live-to-local
# To sync local-to-live: python manage.py sync_databases --direction=local-to-live


class Command(BaseCommand):
    help = "Sync databases between live and local"

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            choices=['live-to-local', 'local-to-live'],
            required=True,
            help="Specify sync direction: 'live-to-local' or 'local-to-live'."
        )

    def handle(self, *args, **options):
        direction = options['direction']
        dump_file = 'db_dump.sql'
        ssh_host = 'ssh.pythonanywhere.com'
        ssh_user = 'sanjoybijoy'
        ssh_password = 'p089chandra'  # Replace with your actual SSH password
        local_port = 3307
        remote_host = 'sanjoybijoy.mysql.pythonanywhere-services.com'
        remote_port = 3306

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.stdout.write("Establishing SSH tunnel...")
            ssh_client.connect(ssh_host, username=ssh_user, password=ssh_password)
            tunnel = ssh_client.get_transport().open_channel(
                "direct-tcpip",
                (remote_host, remote_port),
                ("localhost", local_port),
            )

            if direction == 'live-to-local':
                self.stdout.write("Dumping live database excluding session table...")
                dump_cmd = (
                    f"mysqldump -u sanjoybijoy -ppm4001chandra "
                    f"-h 127.0.0.1 --port={local_port} sanjoybijoy$stockiq_01 "
                    f"--ignore-table=sanjoybijoy$stockiq_01.django_session > {dump_file}"
                )
                subprocess.call(dump_cmd, shell=True)

                self.stdout.write("Importing into local database...")
                import_cmd = (
                    f"mysql -u root -pm4001chandra stockiq_01 < {dump_file}"
                )
                subprocess.call(import_cmd, shell=True)

            elif direction == 'local-to-live':
                self.stdout.write("Dumping local database excluding session table...")
                dump_cmd = (
                    f"mysqldump -u root -pm4001chandra "
                    f"--ignore-table=stockiq_01.django_session stockiq_01 > {dump_file}"
                )
                subprocess.call(dump_cmd, shell=True)

                self.stdout.write("Importing into live database...")
                import_cmd = (
                    f"mysql -u sanjoybijoy -ppm4001chandra "
                    f"-h 127.0.0.1 --port={local_port} sanjoybijoy$stockiq_01 < {dump_file}"
                )
                subprocess.call(import_cmd, shell=True)

        finally:
            self.stdout.write("Cleaning up...")
            if os.path.exists(dump_file):
                os.remove(dump_file)
            if tunnel is not None:
                tunnel.close()
            ssh_client.close()
            self.stdout.write("Database sync completed.")
