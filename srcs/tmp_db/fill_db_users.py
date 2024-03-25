# users_db_creation.py

import os
import sys
import csv
import django

from pathlib import Path
sys.path.append(Path(__file__).resolve().parent.parent.__str__())

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'srcs.settings')

django.setup()

# from django.contrib.auth.models import User
# from django.contrib.auth import get_user_model
from user_management.models import Player

def import_users(csv_file):
	try:
		with open(csv_file, 'r') as file:
			reader = csv.reader(file)
			for row in reader:
				if len(row) != 4:
					print("Invalid CSV format. Each row should have three columns: username, email, password")
					return
				username, email, password, avatar_file = row
				# Player = get_user_model()
				if Player.objects.filter(username=username).exists():
					print(f'User "{username}" already exists')
				else:
					Player.objects.create_user(username=username, email=email, password=password, avatar_file=avatar_file)
					print(f'User "{username}" created successfully')
	except FileNotFoundError:
		print("File not found. Please provide a valid CSV file path.")

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage: python users_db_creation.py <csv_file>")
		sys.exit(1)
	csv_file = sys.argv[1]
	import_users(csv_file)