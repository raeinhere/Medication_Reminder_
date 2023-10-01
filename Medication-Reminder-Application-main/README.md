# Medication-Reminder-Application

## How to install
To install and set up the Medication Reminder application, follow these steps:
1.	Clone the repository from GitHub: https://github.com/Jan-Jsr/Medication-Reminder-Application
2.	Install the required dependencies by running the following command:
pip install -r requirements.txt
3.	Configure the database connection in the app.py file. Modify the SQLALCHEMY_DATABASE_URI variable to match your database configuration.
4.	Run the database migrations by executing the following commands:
flask db init
flask db migrate
flask db upgrade

## How to run
To run the Medication Reminder application, use the following command:
flask run
or simply run app.py.
The application will be accessible at http://localhost:5000 in your web browser.
