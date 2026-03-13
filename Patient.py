import random
import pyodbc
import string
from Person import PersonManager
from PyQt5.QtWidgets import QMessageBox

person_manager = PersonManager()
patients_array = []  # Global array to store Patient objects

#   PATIENT DATA CLASS
class Patient:
    """Simple Patient data class for frontend access."""
    def __init__(self, patient_id, name, password, gender, age, smoker, children,
                 weight, height, guardian_name, guardian_contact, caretaker_id,
                 caretaker_notes, region, picture):
        self.Patient_ID = patient_id
        self.name = name
        self.password = password
        self.gender = gender
        self.age = age
        self.smoker = smoker
        self.children = children
        self.weight = weight
        self.height = height
        self.guardian_name = guardian_name
        self.guardian_contact = guardian_contact
        self.caretaker_id = caretaker_id
        self.caretaker_notes = caretaker_notes
        self.region = region
        self.picture = picture


#   PATIENT MANAGER
class PatientManager:
    rand = random.Random()

    def __init__(self):
        self.db_path = r"D:\Aiza-NED\Data Structures and Algorithms\DSA_Carefree\Carefree_Database.accdb"

        # --- FIXED CONNECTION STRING ---
        self.conn_str = (
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            rf"DBQ={self.db_path};"
        )

        person_manager.connect_db()

    #   Generate unique random patient ID
    def generate_id(self):
        while True:
            random_num = random.randint(10000, 99999)
            new_id = f"P-{random_num}"

            conn = pyodbc.connect(self.conn_str)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Patient WHERE Patient_ID=?", (new_id,))
            exists = cur.fetchone()[0]
            conn.close()

            if exists == 0:
                return new_id

    #   Add Patient
    def add_patient(self, name, gender, age, smoker, children, caretaker_id,
                weight, height, guardian_name, guardian_contact, region):
        patient_id = self.generate_id()
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        if not region:
            region = "northeast"  # default region if combo box is empty

        try:
            conn = pyodbc.connect(self.conn_str)
            cur = conn.cursor()

            query = """INSERT INTO Patient 
                       (Patient_ID, Patient_Name, Guardian_Password, Age, Patient_Gender,
                        Guardian_Name, Patient_Smoker, Patient_Children, Patient_Height,
                        Patient_Weight, Guardian_Contact, Patient_Region, C_ID)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

            cur.execute(query, (
                patient_id, name, password, age, gender,
                guardian_name, smoker, children, height, weight,
                guardian_contact, region, caretaker_id
            ))

            conn.commit()
            conn.close()

            # store in local array with correct order
            new_patient = Patient(
                patient_id=patient_id,
                name=name,
                password=password,
                gender=gender,
                age=int(age),
                smoker=smoker,
                children=int(children),
                weight=float(weight),
                height=float(height),
                guardian_name=guardian_name,
                guardian_contact=guardian_contact,
                caretaker_id=str(caretaker_id),
                caretaker_notes=None,
                region=region,
                picture=None
            )
            patients_array.append(new_patient)

            QMessageBox.information(None, "Guardian password", f"Guardian password is: {password}")

            return True

        except Exception as e:
            print("Failed to add patient:", e)
            return False


    #   Update Patient
    def update_patient(self, patient_id, name, gender, age, smoker,
                       children, weight, height, guardian_name,
                       guardian_contact, region):

        try:
            conn = pyodbc.connect(self.conn_str)
            cur = conn.cursor()

            query = """UPDATE Patient SET 
                        Patient_Name=?, Patient_Gender=?, Age=?, 
                        Patient_Smoker=?, Patient_Children=?, 
                        Patient_Weight=?, Patient_Height=?,
                        Guardian_Name=?, Guardian_Contact=?, Patient_Region=?
                       WHERE Patient_ID=?"""

            cur.execute(query, (
                name, gender, age, smoker, children,
                weight, height, guardian_name, guardian_contact,
                region, patient_id
            ))

            conn.commit()
            conn.close()

            # update local array
            p = self.get_patient_by_id(patient_id)
            if p:
                p.name = name
                p.gender = gender
                p.age = age
                p.smoker = smoker
                p.children = children
                p.weight = weight
                p.height = height
                p.guardian_name = guardian_name
                p.guardian_contact = guardian_contact
                p.region = region

            return True

        except Exception as e:
            print("Failed to update patient:", e)
            return False

    #   Load ALL Patients
    def load_patient_information(self):
        global patients_array
        patients_array.clear()

        try:
            conn = pyodbc.connect(self.conn_str)
            cur = conn.cursor()

            cur.execute("""
                SELECT Patient_ID, Patient_Name, Guardian_Password, Patient_Gender, Age,
                       Patient_Smoker, Patient_Children, Patient_Weight, Patient_Height,
                       Guardian_Name, Guardian_Contact, C_ID, Guardian_Comment, Patient_Region,
                       Patient_Picture
                FROM Patient
            """)

            rows = cur.fetchall()

            for row in rows:
                # Match order exactly with Patient constructor
                p = Patient(
                    patient_id=row[0],
                    name=row[1],
                    password=row[2],
                    gender=row[3],
                    age=row[4],
                    smoker=row[5],
                    children=row[6],
                    weight=row[7],
                    height=row[8],
                    guardian_name=row[9],
                    guardian_contact=row[10],
                    caretaker_id=row[11],
                    caretaker_notes=row[12],
                    region=row[13],
                    picture=row[14]
                )
                patients_array.append(p)

            conn.close()
            print(f"Loaded {len(patients_array)} patients.")

        except Exception as e:
            print("Failed to load patients:", e)


    #   Get Patient By ID
    def get_patient_by_id(self, patient_id):
        for p in patients_array:
            if p.Patient_ID == patient_id:
                return p
        return None

    # Delete Patient
    def delete_patient(self, patient_id):
        try:
            conn = pyodbc.connect(self.conn_str)
            cur = conn.cursor()

            cur.execute("DELETE FROM Patient WHERE Patient_ID=?", (patient_id,))
            conn.commit()
            conn.close()

            # remove from array
            global patients_array
            patients_array = [p for p in patients_array if p.Patient_ID != patient_id]

            return True

        except Exception as e:
            print("Failed to delete patient:", e)
            return False
