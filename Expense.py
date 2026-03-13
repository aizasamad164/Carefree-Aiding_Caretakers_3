import random
import pyodbc
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox


class ExpenseManager:
    def __init__(self):
        # Stack to store expenses (LIFO - Last In First Out)
        self.expense_stack = []
        self.used_ids = []
        self.current_patient_id = None
        # Update this path to match your project's database location
        self.db_path = r"D:\Aiza-NED\Data Structures and Algorithms\DSA_Carefree\Carefree_Database.accdb"
        self.conn = None
        self.cursor = None
        self.connect_db()
    

    # STACK OPERATIONS    
    def push(self, expense_item):
        """Push expense onto stack (add to top)"""
        self.expense_stack.append(expense_item)
    
    def pop(self):
        """Pop expense from stack (remove from top)"""
        if not self.expense_stack:
            return None
        return self.expense_stack.pop()
    
    def peek(self):
        """View top expense without removing"""
        if not self.expense_stack:
            return None
        return self.expense_stack[-1]
    
    def is_empty(self):
        """Check if stack is empty"""
        return len(self.expense_stack) == 0
    
    def size(self):
        """Get stack size"""
        return len(self.expense_stack)
    
    def get_all_expenses(self):
        """Get all expenses from stack (top to bottom order)"""
        return list(reversed(self.expense_stack))
    
    def connect_db(self):
        """Connect to Access Database"""
        try:
            self.conn = pyodbc.connect(
                r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
                fr"DBQ={self.db_path};"
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            print("DB Connection Error:", e)
    
    # ID GENERATION    
    def generated_expenses_id(self):
        """Generate unique expense ID"""
        while True:
            id_num = random.randint(1, 9999)
            if id_num not in self.used_ids:
                self.used_ids.append(id_num)
                return id_num
    

    # ADD EXPENSE TO STACK    
    def add_expense(self, name, category, amount, expense_datetime, current_patient_id):
        """Add expense to stack"""
        if not name.strip():
            return False
        
        # Generate unique ID
        expense_id = f"E-{self.generated_expenses_id()}"
        
        # Create expense tuple: (expense_id, name, category, amount, datetime, patient_id)
        expense_item = (expense_id, name, category, amount, expense_datetime, self.current_patient_id)
        
        # Push to stack
        self.push(expense_item)
        return True
    

    # REMOVE EXPENSE FROM STACK    
    def remove_expense(self, expense_id):
        """Remove expense from stack by name and category"""
        temp = []
        found = False
    
        while not self.is_empty():
            e = self.pop()
            if e[0] == expense_id:
                found = True
                continue
            temp.append(e)

        while temp:
            self.push(temp.pop())

        return found

    
    # LOAD EXPENSES FROM DB    
    def load_expenses_by_patient(self, patient_id):
        """Load expenses from database for a specific patient"""
        if not self.cursor:
            return
    
        self.expense_stack.clear()
        self.current_patient_id = patient_id
    
        try:
            self.cursor.execute("""
                SELECT Expense_ID, Expense_Name, Expense_Category, Exepense_Amount, Expense_Time, P_ID
                FROM Expenses
                WHERE P_ID = ?
            """, (patient_id,))

            rows = self.cursor.fetchall()  # fetch all rows once

            for expense_id, name, category, amount, expense_time, pid in rows:
                # parse datetime
                if isinstance(expense_time, str):
                    try:
                        expense_time = datetime.strptime(expense_time, "%m/%d/%Y %I:%M:%S %p")
                    except ValueError:
                        try:
                            expense_time = datetime.strptime(expense_time, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            expense_time = datetime.now()

                try:
                    amount = float(amount)
                except (TypeError, ValueError):
                    amount = 0

                expense_item = (expense_id, name, category, amount, expense_time, pid)
                self.push(expense_item)

        except Exception as e:
            print("DB Load Error:", e)

    
    # SAVE EXPENSES TO DB    
    def save_expenses_to_db(self):
        """Save all expenses from stack to database, replacing old records"""
        if not self.cursor or not self.current_patient_id:
            return

        try:
            # Delete old expenses for this patient
            self.cursor.execute("DELETE FROM Expenses WHERE P_ID = ?", (self.current_patient_id,))

            # Insert all expenses from stack
            for expense_id, name, category, amount, expense_time, pid in self.expense_stack:
                time_str = expense_time.strftime("%Y-%m-%d %H:%M:%S")  # or "%m/%d/%Y %I:%M:%S %p" if you prefer
                self.cursor.execute(
                    """
                    INSERT INTO Expenses 
                    (Expense_ID, Expense_Name, Expense_Category, Exepense_Amount, Expense_Time, P_ID)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (expense_id, name, category, amount, time_str, pid)
                )

            self.conn.commit()
            self.update_patient_total_expenses(self.current_patient_id)

        except Exception as e:
            print("DB Save Error:", e)


    
    # get expenses    
    def get_expenses(self):
        """Return all expenses in the stack as a list of tuples"""
        expenses = []
    
        for expense_item in self.expense_stack:
            # ensure each tuple has exactly 6 elements
            if len(expense_item) == 6:
                expenses.append(expense_item)
            else:
                # ignore malformed entries
                continue
    
        # sort by date (most recent first)
        expenses.sort(key=lambda x: x[4], reverse=True)  # x[4] is datetime
        return expenses
    
    # ===== UPDATE PATIENT TOTAL EXPENSES =====
    
    def update_patient_total_expenses(self, patient_id):
        """Update total expenses (Charges) in Patient table"""
        if not self.cursor:
            return
        
        total_expenses = 0
        
        try:
            # Calculate total from database (more reliable)
            self.cursor.execute(
                "SELECT SUM(Exepense_Amount) FROM Expenses WHERE P_ID = ?",
                (patient_id,)
            )
            result = self.cursor.fetchone()
            
            if result[0] is not None:
                total_expenses = float(result[0])
            
            # Update Patient table
            self.cursor.execute(
                "UPDATE Patient SET Charges = ? WHERE Patient_ID = ?",
                (total_expenses, patient_id)
            )
            self.conn.commit()
        
        except Exception as e:
            print("Error updating patient total expenses:", e)



