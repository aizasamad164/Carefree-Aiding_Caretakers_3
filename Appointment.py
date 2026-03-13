import pyodbc
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

# Node for linked list
class AppointmentNode:
    def __init__(self, dt, name, category, patient_id, desc):
        self.datetime_val = dt
        self.client_name = name
        self.category = category
        self.patient_id = patient_id
        self.description = desc
        self.next = None

# Linked list organized by category
class AppointmentLinkedList:
    def __init__(self):
        self.heads = {
            "Consultation": None,
            "Follow-up": None,
            "Medical Test": None,
            "Therapy": None,
            "Emergency": None
        }

    # Add appointment node
    def add(self, dt, name, category, pid, desc):
        node = AppointmentNode(dt, name, category, pid, desc)
        if not self.heads[category]:
            self.heads[category] = node
        else:
            current = self.heads[category]
            while current.next:
                current = current.next
            current.next = node

    # Remove appointment node
    def remove(self, name, category=None):
        categories = [category] if category else self.heads.keys()
        for cat in categories:
            if cat not in self.heads:
                # Show an error instead of crashing
                print(f"Error: Invalid appointment category '{cat}'")
                return False
        
            current = self.heads[cat]
            prev = None
            while current:
                if current.client_name == name:
                    if prev:
                        prev.next = current.next
                    else:
                        self.heads[cat] = current.next
                    return True
                prev = current
                current = current.next

    # Get all appointments in nodes
    def get_all(self):
        result = []
        for cat in self.heads:
            current = self.heads[cat]
            while current:
                result.append((current.datetime_val, current.client_name, current.category, current.patient_id, current.description))
                current = current.next
        return result


class AppointmentManager:
    def __init__(self):
        self.current_patient_id = None
        self.appointments = AppointmentLinkedList()
        self.db_path = r"D:\Aiza-NED\Data Structures and Algorithms\DSA_Carefree\Carefree_Database.accdb"
        self.conn = None
        self.cursor = None
        self.connect_db()

    # Connect to Access Database 
    def connect_db(self):
        try:
            self.conn = pyodbc.connect(
                r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
                fr"DBQ={self.db_path};"
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            print("DB Connection Error:", e)

    # Add Appointment to linked list 
    def add_appointment(self, name, category, dt, pid, desc):
        if not name.strip() or not desc.strip():
            return False
        self.appointments.add(dt, name, category, pid, desc)  # this is fine

    # Remove Appointment from linked list
    def remove_appointment(self, name, category=None):
        found = self.appointments.remove(name, category)
        if found:
            QMessageBox.information(None, "Removed", f"Appointment '{name}' removed successfully.")
        else:
            QMessageBox.warning(None, "Not Found", f"No appointment found with name '{name}'")
        return found

    # Load appointments from db for a patient 
    def load_appointments_by_patient(self, patient_id):
        if not self.cursor:
            return
        self.current_patient_id = patient_id
        self.appointments = AppointmentLinkedList()  # clear existing
        try:
            self.cursor.execute(
                "SELECT Client_Name, Appointment_Category, Appointment_DateTime, P_ID, Appointment_Description "
                "FROM Appointment WHERE P_ID = ?", (patient_id,)
            )
            rows = self.cursor.fetchall()
            for name, category, dt, pid, desc in rows:
                if isinstance(dt, str):
                    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                self.appointments.add(dt, name, category, pid, desc)
        except Exception as e:
            print("DB Load Error:", e)

    # Get filtered appointments based on time frame 
    def get_filtered_appointments(self, filter_type="All"):
        now = datetime.now()
        filtered = []
        for dt, name, category, pid, desc in self.appointments.get_all():
            include = True
            if filter_type == "Today":
                include = dt.date() == now.date()
            elif filter_type == "Weekly":
                days_diff = (dt.date() - now.date()).days
                include = 0 <= days_diff < 7  # next 7 days; change to abs(days_diff) < 7 for past+future
            elif filter_type == "Monthly":
                include = dt.year == now.year and dt.month == now.month
            if include:
                filtered.append((dt, name, category, pid, desc))
        return sorted(filtered, key=lambda x: x[0])


    # Save appointments to db
    def save_appointments_to_db(self):
        if not self.cursor or not self.current_patient_id:
            return
        try:
            # Delete old appointments for the patient
            self.cursor.execute("DELETE FROM Appointment WHERE P_ID = ?", (self.current_patient_id,))
            # Insert from linked list
            for dt, name, category, pid, desc in self.appointments.get_all():
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute(
                    "INSERT INTO Appointment (Client_Name, Appointment_Category, Appointment_DateTime, P_ID, Appointment_Description) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (name, category, dt_str, pid, desc)
                )
            self.conn.commit()
        except Exception as e:
            print("DB Save Error:", e)
