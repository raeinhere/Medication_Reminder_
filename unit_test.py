import unittest
from flask import session
from app import app, db, MedicationEntry, User, Reminder


class AppTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()  # Set up the application context
        self.app_context.push()  # Push the application context
        db.create_all()  # Now create all database tables
        self.client = app.test_client()

    '''
        def setUp(self):
            app.config['TESTING'] = True
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            db.create_all()
            self.client = app.test_client()
            self.app_context = app.app_context()
            self.app_context.push()
    '''
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_medication_entry(self):
        with app.test_request_context():
            # Create a test user
            user = User(username='testuser', password='password', email='test@example.com')
            db.session.add(user)
            db.session.commit()

            # Simulate user login
            with self.client.session_transaction() as sess:
                sess['user_id'] = user.id

            # Send a POST request to add a medication entry
            response = self.client.post('/add', data={
                'name': 'Medicine A',
                'dosage': '10mg',
                'frequency': '1/day',
                'start_date': '2023-07-01',
                'end_date': '2023-07-10'
            }, follow_redirects=True)

            # Assert that the medication entry is successfully added
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Medication entry added successfully!', response.data)
            self.assertEqual(len(user.medication_entries), 1)

            medication_entry = user.medication_entries[0]
            self.assertEqual(medication_entry.name, 'Medicine A')
            self.assertEqual(medication_entry.dosage, '10mg')
            self.assertEqual(medication_entry.frequency, '1/day')
            self.assertEqual(medication_entry.start_date.strftime('%Y-%m-%d'), '2023-07-01')
            self.assertEqual(medication_entry.end_date.strftime('%Y-%m-%d'), '2023-07-10')

    def test_delete_medication_entry(self):
        with app.test_request_context():
            # Create a test user and medication entry
            user = User(username='testuser', password='password', email='test@example.com')
            medication_entry = MedicationEntry(name='Medicine A', dosage='10mg', frequency='1/day',
                                               start_date='2023-07-01', end_date='2023-07-10', user=user)
            db.session.add(user)
            db.session.add(medication_entry)
            db.session.commit()

            # Simulate user login
            with self.client.session_transaction() as sess:
                sess['user_id'] = user.id

            # Send a POST request to delete the medication entry
            response = self.client.post(f'/delete/{medication_entry.id}', follow_redirects=True)

            # Assert that the medication entry is successfully deleted
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Medication entry deleted successfully!', response.data)
            self.assertEqual(len(user.medication_entries), 0)

    def test_add_reminder(self):
        with app.test_request_context():
            # Create a test user and medication entry
            user = User(username='testuser', password='password', email='test@example.com')
            medication_entry = MedicationEntry(name='Medicine A', dosage='10mg', frequency='1/day',
                                               start_date='2023-07-01', end_date='2023-07-10', user=user)
            db.session.add(user)
            db.session.add(medication_entry)
            db.session.commit()

            # Simulate user login
            with self.client.session_transaction() as sess:
                sess['user_id'] = user.id

            # Send a POST request to add a reminder
            response = self.client.post(f'/add-reminder/{medication_entry.id}', data={
                'reminder_date': '2023-07-05',
                'reminder_time': '08:00'
            }, follow_redirects=True)

            # Assert that the reminder is successfully added
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Reminder added successfully!', response.data)
            self.assertEqual(len(medication_entry.reminders), 1)

            reminder = medication_entry.reminders[0]
            self.assertEqual(reminder.time.strftime('%Y-%m-%d %H:%M'), '2023-07-05 11:00')


    def test_delete_reminder(self):
        with app.test_request_context():
            # Create a test user, medication entry, and reminder
            user = User(username='testuser', password='password', email='test@example.com')
            medication_entry = MedicationEntry(name='Medicine A', dosage='10mg', frequency='1/day',
                                               start_date='2023-07-01', end_date='2023-07-10', user=user)
            reminder = Reminder(time='2023-07-05 08:00', medication_entry=medication_entry)
            db.session.add(user)
            db.session.add(medication_entry)
            db.session.add(reminder)
            db.session.commit()

            # Simulate user login
            with self.client.session_transaction() as sess:
                sess['user_id'] = user.id

            # Send a POST request to delete the reminder
            response = self.client.post(f'/delete-reminder/{reminder.id}', follow_redirects=True)

            # Assert that the reminder is successfully deleted
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Reminder deleted successfully!', response.data)
            self.assertEqual(len(medication_entry.reminders), 0)


if __name__ == '__main__':
    unittest.main()
