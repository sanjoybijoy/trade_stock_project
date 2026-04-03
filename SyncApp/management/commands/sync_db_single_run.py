from django.core.management.base import BaseCommand
import os
import subprocess
import paramiko

# Before sync you should connect through ssh tunnel to pythonanywhere
# Run the following command in Command Prompt 
# ssh -L 3307:sanjoybijoy.mysql.pythonanywhere-services.com:3306 sanjoybijoy@ssh.pythonanywhere.com
# Uses:
# To sync live-to-local and local-to-live in a single run: python manage.py sync_db_single_run


class Command(BaseCommand):
    help = "Sync databases between live and local (both directions in a single run)"

    def handle(self, *args, **options):
        live_to_local_dump_file = 'live_to_local_dump.sql'
        local_to_live_dump_file = 'local_to_live_dump.sql'
        ssh_host = 'ssh.pythonanywhere.com'
        ssh_user = 'sanjoybijoy'
        ssh_password = 'p089chandra'  # Replace with your actual SSH password
        local_port = 3307
        remote_host = 'sanjoybijoy.mysql.pythonanywhere-services.com'
        remote_port = 3306

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Establish SSH Tunnel
            self.stdout.write("Establishing SSH tunnel...")
            ssh_client.connect(ssh_host, username=ssh_user, password=ssh_password)
            tunnel = ssh_client.get_transport().open_channel(
                "direct-tcpip",
                (remote_host, remote_port),
                ("localhost", local_port),
            )

            # Step 1: Sync live-to-local
            self.stdout.write("Starting live-to-local database synchronization...")
            self.stdout.write("Dumping live database excluding session table...")
            live_dump_cmd = (
                f"mysqldump -u sanjoybijoy -ppm4001chandra "
                f"-h 127.0.0.1 --port={local_port} sanjoybijoy$stockiq_01 "
                f"--ignore-table=sanjoybijoy$stockiq_01.django_session > {live_to_local_dump_file}"
            )
            subprocess.call(live_dump_cmd, shell=True)

            self.stdout.write("Importing into local database...")
            local_import_cmd = (
                f"mysql -u root -pm4001chandra stockiq_01 < {live_to_local_dump_file}"
            )
            subprocess.call(local_import_cmd, shell=True)

            # Step 2: Sync local-to-live
            self.stdout.write("Starting local-to-live database synchronization...")
            self.stdout.write("Dumping local database excluding session table...")
            local_dump_cmd = (
                f"mysqldump -u root -pm4001chandra "
                f"--ignore-table=stockiq_01.django_session stockiq_01 > {local_to_live_dump_file}"
            )
            subprocess.call(local_dump_cmd, shell=True)

            self.stdout.write("Importing into live database...")
            live_import_cmd = (
                f"mysql -u sanjoybijoy -ppm4001chandra "
                f"-h 127.0.0.1 --port={local_port} sanjoybijoy$stockiq_01 < {local_to_live_dump_file}"
            )
            subprocess.call(live_import_cmd, shell=True)

        finally:
            # Cleanup
            self.stdout.write("Cleaning up...")
            if os.path.exists(live_to_local_dump_file):
                os.remove(live_to_local_dump_file)
            if os.path.exists(local_to_live_dump_file):
                os.remove(local_to_live_dump_file)
            if tunnel is not None:
                tunnel.close()
            ssh_client.close()
            self.stdout.write("Database sync completed (both directions).")
