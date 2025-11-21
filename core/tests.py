from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta
from .models import Belt, Trainee, Event, Match, Payment, Promotion


class DashboardStatisticsTestCase(TestCase):
    """Test cases for admin dashboard statistics"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user and group
        self.admin_group = Group.objects.create(name='Admin')
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.groups.add(self.admin_group)
        
        # Create belt
        self.belt = Belt.objects.create(name='White', order=1)
        
        # Create test trainees
        for i in range(5):
            user = User.objects.create_user(
                username=f'trainee{i}',
                password='testpass123'
            )
            Trainee.objects.create(
                user=user,
                date_of_birth=timezone.now().date() - timedelta(days=365*20),
                belt=self.belt,
                contact_number='1234567890',
                address='Test Address',
                is_active=True
            )
        
        # Create upcoming event
        Event.objects.create(
            name='Test Tournament',
            description='Test Description',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=8),
            location='Test Location',
            is_published=True
        )
        
        # Create pending payment
        trainee = Trainee.objects.first()
        Payment.objects.create(
            trainee=trainee,
            amount=100.00,
            date=timezone.now().date(),
            description='Monthly Fee',
            paid=False
        )
        
        # Create recent promotion
        Promotion.objects.create(
            trainee=trainee,
            belt_from=self.belt,
            belt_to=self.belt,
            date=timezone.now().date() - timedelta(days=5)
        )
        
        self.client = Client()
    
    def test_dashboard_statistics_requires_admin(self):
        """Test that dashboard statistics requires admin authentication"""
        response = self.client.get('/api/dashboard/statistics/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_statistics_returns_correct_data(self):
        """Test that dashboard statistics returns correct aggregated data"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/api/dashboard/statistics/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '5')  # 5 active trainees
        self.assertContains(response, '1')  # 1 upcoming event
    
    def test_admin_dashboard_loads(self):
        """Test that admin dashboard page loads successfully"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/dashboard/admin/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Dashboard')
        self.assertContains(response, 'Quick Actions')
    
    def test_dashboard_statistics_htmx_request(self):
        """Test that HTMX requests return partial template"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(
            '/api/dashboard/statistics/',
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        # Should contain statistics but not full page structure
        self.assertContains(response, 'Total Trainees')
        self.assertNotContains(response, '<!DOCTYPE html>')
