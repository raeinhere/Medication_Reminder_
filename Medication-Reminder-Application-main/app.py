from flask import Flask, render_template, request, redirect, flash, session
from flask_migrate import Migrate

from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import pytz
import time

# set up a backend scheduler
scheduler = BackgroundScheduler()
scheduler.start()

app = Flask(__name__, static_url_path='/static')
app.secret_key = '123456'


# Configure database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://people:123456@localhost/medication_reminder'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Medication Entry model
class MedicationEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    medication_entries = db.relationship('MedicationEntry', backref='user', lazy=True)

# Reminder model
class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, nullable=False)

    medication_entry_id = db.Column(db.Integer, db.ForeignKey('medication_entry.id'), nullable=False)
    medication_entry = db.relationship('MedicationEntry', backref=db.backref('reminders', cascade='all, delete-orphan', lazy=True))

@app.route('/add-reminder/<int:entry_id>', methods=['GET', 'POST'])
def add_reminder(entry_id):
    if 'user_id' not in session:
        return redirect('/login')


    #medication_entry = db.session.query(MedicationEntry).get(entry_id)
    medication_entry = db.session.get(MedicationEntry, entry_id)

    if medication_entry and medication_entry.user_id == session['user_id']:
        if request.method == 'POST':
            reminder_time = request.form.get('reminder_time')
            reminder_date = request.form.get('reminder_date')
            
            
            print("Reminder Date:", reminder_date)
            print("Reminder Time:", reminder_time)

            # Combine date and time to create reminder datetime object
            reminder_datetime = datetime.strptime(f'{reminder_date} {reminder_time}', '%Y-%m-%d %H:%M')
            
            # Convert reminder datetime to PDT timezone
            pacific_tz = pytz.timezone('America/Los_Angeles')
            reminder_datetime = pacific_tz.localize(reminder_datetime)

            # Create new reminder and associate it with the medication entry
            reminder = Reminder(time=reminder_datetime, medication_entry=medication_entry)
            db.session.add(reminder)
            db.session.commit()

            flash('Reminder added successfully!', 'success')

            return redirect('/add-reminder/' + str(entry_id))
        reminders = Reminder.query.filter_by(medication_entry_id=entry_id).all()
        return render_template('add-reminder.html', medication_entry=medication_entry,reminders=reminders)

    else:
        flash('Invalid medication entry!', 'error')
        return redirect('/')

# Delete reminder
@app.route('/delete-reminder/<int:reminder_id>', methods=['POST','GET'])
def delete_reminder(reminder_id):
    if 'user_id' not in session:
        return redirect('/login')


    #reminder = db.session.query(Reminder).get(reminder_id)
    reminder = db.session.get(Reminder, reminder_id)

    if reminder and reminder.medication_entry.user_id == session['user_id']:
        db.session.delete(reminder)
        db.session.commit()

        flash('Reminder deleted successfully!', 'success')

    return redirect('/add-reminder/' + str(reminder.medication_entry_id))

# Send reminders
@app.route('/send-reminder/<int:entry_id>', methods=['POST','GET'])
def send_reminders(entry_id):
    if 'user_id' not in session:
        return redirect('/login')


    #medication_entry = db.session.query(MedicationEntry).get(entry_id)
    medication_entry = db.session.get(MedicationEntry, entry_id)

    if medication_entry and medication_entry.user_id == session['user_id']:
        reminders = Reminder.query.filter_by(medication_entry_id=entry_id).all()

        # Send email reminders for each reminder
        for reminder in reminders:
            send_email_job(medication_entry.user.email, medication_entry.name, reminder.time)

        flash('Reminders sent successfully!', 'success')

        return redirect('/add-reminder/' + str(entry_id))

    else:
        flash('Invalid medication entry!', 'error')
        return redirect('/')


# Send email reminders
def send_email_job(email, medication_name, reminder_time):
    # Set up email details
    sender_email = 'ruiningfeng62@gmail.com'
    sender_password = 'kinwnoxzvgjbiobn'
    subject = 'Medication Reminder'
    message = f"Reminder: It's time to take your medication - {medication_name}."

    # Calculate the time difference between the reminder time and the current time
    pacific_tz = pytz.timezone('America/Los_Angeles')

    # retrieve PDT time diff
    current_datetime = datetime.now(pacific_tz)
    reminder_time = pacific_tz.localize(reminder_time)
    time_diff = (reminder_time - current_datetime).total_seconds()

    # If the reminder time has already passed, send the email immediately
    if time_diff <= 0:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
    else:
        # Wait until the reminder time
        time.sleep(time_diff)

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)

# Home page
@app.route('/', methods=['GET','POST'])
def index():
    if 'user_id' in session:
        #user = db.session.query(User).get(session['user_id'])
        user = db.session.get(User, session['user_id'])

        medication_entries = user.medication_entries
        return render_template('index.html', medication_entries=medication_entries,current_user=user)
    else:
        return redirect('/login')

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if the username or email is already registered
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect('/register')

        if existing_email:
            flash('Email already exists. Please choose a different email address.', 'error')
            return redirect('/register')

        # Create a new user
        user = User(username=username, password=password, email=email)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id

        flash('Registration successful!', 'success')
        return redirect('/')

    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username and password match
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Invalid username or password. Please try again.', 'error')
            return redirect('/login')

    return render_template('login.html')

# User logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect('/login')

# Add medication entry
@app.route('/add', methods=['GET', 'POST'])
def add_medication():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        dosage = request.form['dosage']
        frequency = request.form['frequency']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None

        #user = db.session.query(User).get(session['user_id'])
        user = db.session.get(User, session['user_id'])

        medication_entry = MedicationEntry(
            name=name,
            dosage=dosage,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            user=user
        )

        db.session.add(medication_entry)
        db.session.commit()

        flash('Medication entry added successfully!', 'success')
        return redirect('/')
    
    return render_template('add_medication.html')

# Edit medication entry
@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit_medication(entry_id):
    if 'user_id' not in session:
        return redirect('/login')

    #medication_entry = db.session.query(MedicationEntry).get(entry_id)
    medication_entry = db.session.get(MedicationEntry, entry_id)

    if medication_entry and medication_entry.user_id == session['user_id']:
        if request.method == 'POST':
            medication_entry.name = request.form['name']
            medication_entry.dosage = request.form['dosage']
            medication_entry.frequency = request.form['frequency']
            medication_entry.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            medication_entry.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None

            db.session.commit()

            flash('Medication entry updated successfully!', 'success')
            return redirect('/')
        
        return render_template('edit_medication.html', medication_entry=medication_entry)
    else:
        flash('Invalid medication entry!', 'error')
        return redirect('/')

# Delete medication entry
@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_medication(entry_id):
    if 'user_id' not in session:
        return redirect('/login')

    #medication_entry = db.session.query(MedicationEntry).get(entry_id)
    medication_entry = db.session.get(MedicationEntry, entry_id)

    if medication_entry and medication_entry.user_id == session['user_id']:
        db.session.delete(medication_entry)
        db.session.commit()
        flash('Medication entry deleted successfully!', 'success')
    else:
        flash('Invalid medication entry!', 'error')
    
    return redirect('/')

def read_drugs_csv():
    drugs = []
    with open('generic_processed.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            drugs.append(row)
    return drugs

@app.route('/drugs', methods=['GET', 'POST'])
def drugs():
    drugs = read_drugs_csv()
    search_term = request.args.get('search')

    if search_term:
        drugs = [drug for drug in drugs if search_term.lower() in drug['slug'].lower()]

    if drugs:
        flash('Search results found for: {}'.format(search_term))
    else:
        flash('No drugs found for: {}'.format(search_term), 'error')

    return render_template('drugs.html', drugs=drugs, search_term=search_term)







if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
