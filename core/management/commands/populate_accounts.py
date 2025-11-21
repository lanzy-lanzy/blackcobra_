from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import Trainee, Belt
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Populate database with sample accounts for Admin, Judge, and Trainees'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting account population...'))

        # Create Groups if they don't exist
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        judge_group, _ = Group.objects.get_or_create(name='Judge')
        trainee_group, _ = Group.objects.get_or_create(name='Trainee')

        # Create Belts if they don't exist
        belts_data = [
            {'name': 'White Belt', 'order': 1, 'color': '#FFFFFF'},
            {'name': 'Yellow Belt', 'order': 2, 'color': '#FFD700'},
            {'name': 'Orange Belt', 'order': 3, 'color': '#FFA500'},
            {'name': 'Green Belt', 'order': 4, 'color': '#00FF00'},
            {'name': 'Blue Belt', 'order': 5, 'color': '#0000FF'},
            {'name': 'Purple Belt', 'order': 6, 'color': '#800080'},
            {'name': 'Brown Belt', 'order': 7, 'color': '#8B4513'},
            {'name': 'Black Belt', 'order': 8, 'color': '#000000'},
        ]

        belts = {}
        for belt_data in belts_data:
            belt, created = Belt.objects.get_or_create(
                name=belt_data['name'],
                defaults={'order': belt_data['order'], 'color': belt_data['color']}
            )
            belts[belt_data['name']] = belt
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created belt: {belt.name}'))

        # Create Admin User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@karateclub.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin: {admin_user.username} (password: admin123)'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user already exists: {admin_user.username}'))
        
        # Ensure admin is in Admin group
        if not admin_user.groups.filter(name='Admin').exists():
            admin_user.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS(f'Added {admin_user.username} to Admin group'))

        # Create Judge Users
        judges_data = [
            {'username': 'judge1', 'first_name': 'John', 'last_name': 'Smith', 'email': 'judge1@karateclub.com'},
            {'username': 'judge2', 'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'judge2@karateclub.com'},
        ]

        for judge_data in judges_data:
            judge_user, created = User.objects.get_or_create(
                username=judge_data['username'],
                defaults={
                    'email': judge_data['email'],
                    'first_name': judge_data['first_name'],
                    'last_name': judge_data['last_name'],
                }
            )
            if created:
                judge_user.set_password('judge123')
                judge_user.save()
                judge_user.groups.add(judge_group)
                self.stdout.write(self.style.SUCCESS(f'Created judge: {judge_user.username} (password: judge123)'))
            else:
                self.stdout.write(self.style.WARNING(f'Judge already exists: {judge_user.username}'))

        # Create Trainee Users
        trainees_data = [
            {'username': 'trainee1', 'first_name': 'Mike', 'last_name': 'Chen', 'email': 'mike.chen@email.com', 'belt': 'White Belt', 'contact': '555-0101', 'address': '123 Main St, City'},
            {'username': 'trainee2', 'first_name': 'Emily', 'last_name': 'Rodriguez', 'email': 'emily.r@email.com', 'belt': 'Yellow Belt', 'contact': '555-0102', 'address': '456 Oak Ave, City'},
            {'username': 'trainee3', 'first_name': 'David', 'last_name': 'Kim', 'email': 'david.kim@email.com', 'belt': 'Orange Belt', 'contact': '555-0103', 'address': '789 Pine Rd, City'},
            {'username': 'trainee4', 'first_name': 'Lisa', 'last_name': 'Patel', 'email': 'lisa.p@email.com', 'belt': 'Green Belt', 'contact': '555-0104', 'address': '321 Elm St, City'},
            {'username': 'trainee5', 'first_name': 'James', 'last_name': 'Wilson', 'email': 'james.w@email.com', 'belt': 'Blue Belt', 'contact': '555-0105', 'address': '654 Maple Dr, City'},
            {'username': 'trainee6', 'first_name': 'Maria', 'last_name': 'Garcia', 'email': 'maria.g@email.com', 'belt': 'Purple Belt', 'contact': '555-0106', 'address': '987 Cedar Ln, City'},
            {'username': 'trainee7', 'first_name': 'Robert', 'last_name': 'Taylor', 'email': 'robert.t@email.com', 'belt': 'Brown Belt', 'contact': '555-0107', 'address': '147 Birch Way, City'},
            {'username': 'trainee8', 'first_name': 'Anna', 'last_name': 'Lee', 'email': 'anna.lee@email.com', 'belt': 'Black Belt', 'contact': '555-0108', 'address': '258 Spruce Ct, City'},
        ]

        for trainee_data in trainees_data:
            trainee_user, created = User.objects.get_or_create(
                username=trainee_data['username'],
                defaults={
                    'email': trainee_data['email'],
                    'first_name': trainee_data['first_name'],
                    'last_name': trainee_data['last_name'],
                }
            )
            
            if created:
                trainee_user.set_password('trainee123')
                trainee_user.save()
                trainee_user.groups.add(trainee_group)

                # Create Trainee profile
                days_ago = random.randint(30, 365)
                join_date = timezone.now().date() - timedelta(days=days_ago)
                birth_year = random.randint(1990, 2010)
                
                Trainee.objects.create(
                    user=trainee_user,
                    date_of_birth=f'{birth_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                    belt=belts[trainee_data['belt']],
                    contact_number=trainee_data['contact'],
                    address=trainee_data['address'],
                    join_date=join_date,
                    emergency_contact=f'{trainee_data["first_name"]} Parent',
                    emergency_phone=f'555-{random.randint(1000, 9999)}',
                    is_active=True,
                )
                
                self.stdout.write(self.style.SUCCESS(f'Created trainee: {trainee_user.username} ({trainee_data["belt"]}) (password: trainee123)'))
            else:
                self.stdout.write(self.style.WARNING(f'Trainee already exists: {trainee_user.username}'))

        self.stdout.write(self.style.SUCCESS('\n=== Account Population Complete ==='))
        self.stdout.write(self.style.SUCCESS('\nLogin Credentials:'))
        self.stdout.write(self.style.SUCCESS('Admin: username=admin, password=admin123'))
        self.stdout.write(self.style.SUCCESS('Judges: username=judge1/judge2, password=judge123'))
        self.stdout.write(self.style.SUCCESS('Trainees: username=trainee1-8, password=trainee123'))
