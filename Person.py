from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QMessageBox
from PyQt5.QtWidgets import QRadioButton, QLineEdit, QComboBox, QWidget, QFileDialog, QPushButton
from PyQt5.QtGui import QPixmap, QIcon

from Task import TaskManager
from datetime import datetime
import pyodbc
import random
import string

task_manager = TaskManager()

class PersonManager:
    def __init__(self):
        self.db_path = r"D:\Aiza-NED\Data Structures and Algorithms\DSA_Carefree\Carefree_Database.accdb"
        self.conn = None
        self.cursor = None
        self.connect_db()
        self.current_patient_id = None
        self.logged_in_username = ""

        self.logged_in_id = []    # store logged-in user id
        self.role = None          # store which role logged in


    def generate_id(self):
        while True:
            random_num = random.randint(10000, 99999)
            new_id = f"C-{random_num}"

            # check if ID already exists
            self.cursor.execute("SELECT COUNT(*) FROM Caretaker WHERE Caretaker_ID=?", (new_id,))
            if self.cursor.fetchone()[0] == 0:
                return new_id

    # Connect to Access Database
    def connect_db(self):
        try:
            self.conn = pyodbc.connect(
                r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
                fr"DBQ={self.db_path};"
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            QMessageBox.critical(None, "Database Error", f"Failed to connect to database:\n{e}")

    #HAFSA
    def get_patients_by_guardian(self, guardian_name, guardian_password):
        try:
            self.cursor.execute(
                "SELECT Patient_ID FROM Patient WHERE Guardian_Name = ? AND Guardian_Password = ?",
                (guardian_name, guardian_password)
            )
            return self.cursor.fetchall()  # list of (Patient_ID, Patient_Name)
        except Exception as e:
            print("DB error fetching guardian patients:", e)
            return []



    # Check username and password in DB for guardian
    def verify_guardian_user(self, username, password):
        # validate input    
        if not username or not password:
            QMessageBox.warning(None, "Invalid Input", "Please enter both username and password.")
            return False

        if not self.cursor:
            QMessageBox.critical(None, "Connection Error", "Database connection not established.")
            return False

        try:
            self.cursor.execute(
                "SELECT Patient_ID FROM Patient WHERE Guardian_Name = ? AND Guardian_Password = ?",
                (username, password)
            )
            row = self.cursor.fetchone()

            if row:
                patient_id = row[0]

                # ⭐ Save in array
                self.logged_in_id.clear()
                self.logged_in_id.append(patient_id)
                self.role = "guardian"
                self.logged_in_username = username

                QMessageBox.information(None, "Login Successful", f"Welcome, {username}!")
                return True

            else:
                QMessageBox.warning(None, "Login Failed", "Username or password is incorrect.")
                return False

        except Exception as e:
            QMessageBox.critical(None, "Query Error", f"Error verifying user:\n{e}")
            return False


    # Check username and password in DB for caretaker
    def verify_caretaker_user(self, username, password):
        if not username or not password:
            QMessageBox.warning(None, "Invalid Input", "Please enter both username and password.")
            return False

        if not self.cursor:
            QMessageBox.critical(None, "Connection Error", "Database connection not established.")
            return False

        try:
            self.cursor.execute(
                "SELECT Caretaker_ID FROM Caretaker WHERE Caretaker_Name = ? AND Caretaker_Password = ?",
                (username, password)
            )
            row = self.cursor.fetchone()

            if row:
                caretaker_id = row[0]

                # ⭐ Save in array
                self.logged_in_id.clear()
                self.logged_in_id.append(caretaker_id)
                self.role = "caretaker"
                self.logged_in_username = username

                QMessageBox.information(None, "Login Successful", f"Welcome, {username}!")
                return True

            else:
                QMessageBox.warning(None, "Login Failed", "Username or password is incorrect.")
                return False

        except Exception as e:
            QMessageBox.critical(None, "Query Error", f"Error verifying user:\n{e}")
            return False



    # create caretaker user in DB
    def create_user(self, username, age, gender, contact, skills):
        if not all([username, int(age), gender.strip(), contact, skills]):
            QMessageBox.warning(None, "Invalid Input", "All fields must be filled.")
            return False

        if not self.cursor:
            QMessageBox.critical(None, "Connection Error", "Database connection not established.")
            return False

        try:
            # Check if username already exists
            self.cursor.execute("SELECT COUNT(*) FROM Caretaker WHERE Caretaker_Name = ?", (username,))
            if self.cursor.fetchone()[0] > 0:
                QMessageBox.warning(None, "Duplicate User", f"Username '{username}' already exists.")
                return False

            # Generate random password (8–10 characters)
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            caretaker_id = self.generate_id()

            # Insert new caretaker
            self.cursor.execute(
                """INSERT INTO Caretaker 
                   (Caretaker_ID, Caretaker_Name, Caretaker_Age, Caretaker_Password, Caretaker_Gender, Caretaker_Contact, Caretaker_Skills) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                (caretaker_id, username, age, password, gender, contact, skills)
            )
            self.conn.commit()

            QMessageBox.information(None, "Caretaker Created", f"Account created for '{username}'.\nGenerated Password: {password}")
            return True

        except Exception as e:
            QMessageBox.critical(None, "Database Error", f"Could not create user:\n{e}")
            return False


    # adeena you will use these two functions too

    # Quick Sort implementation to sort patients by ID number
    def quick_sort_patients(self, arr):
        if len(arr) <= 1:
            return arr

        # Middle element as pivot
        pivot = arr[len(arr) // 2]
        pivot_id_num = int(pivot[0].split("-")[1])

        # Partitioning
        left, middle, right = [], [], []

        # Partition based on patient ID number
        for item in arr:
            pid_num = int(item[0].split("-")[1])
            if pid_num < pivot_id_num:
                left.append(item)
            elif pid_num > pivot_id_num:
                right.append(item)
            else:
                middle.append(item)

        return self.quick_sort_patients(left) + middle + self.quick_sort_patients(right)

    # Binary Search implementation to find patients by name prefix
    def prefix_binary_search(self, arr, prefix):
        # Normalize prefix for case-insensitive comparison
        prefix = prefix.strip().lower()
        
        low, high = 0, len(arr) - 1
        result_index = -1

        while low <= high:
            mid = (low + high) // 2
            mid_name = arr[mid][1].lower()
            
            # Check if the name starts with the prefix and adjust search range until the first match is found
            if mid_name.startswith(prefix):
                result_index = mid
                high = mid - 1
            elif mid_name < prefix:
                low = mid + 1
            else:
                high = mid - 1

        return result_index


    def clear_page(self, page_widget):
        """
        Clears all input widgets inside a given page of QStackedWidget.
    
        page_widget: the QWidget (page) inside stackedWidget
        """
        for widget in page_widget.findChildren(QWidget):
            # Clear text fields
            if isinstance(widget, QLineEdit):
                widget.clear()
            # Reset combo boxes
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            # Uncheck radio buttons
            elif isinstance(widget, QRadioButton):
                widget.setAutoExclusive(False)
                widget.setChecked(False)
                widget.setAutoExclusive(True)  


    