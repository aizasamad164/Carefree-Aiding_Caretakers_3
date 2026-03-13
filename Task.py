#import heapq
import itertools
import pyodbc
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox

class TaskManager:
    def __init__(self):
        self.tasks = []
        self.counter = itertools.count()  # unique insertion counter for tie-breaking
        self.current_patient_id = None
        self.db_path = r"D:\Aiza-NED\Data Structures and Algorithms\DSA_Carefree\Carefree_Database.accdb"
        self.conn = None
        self.cursor = None
        self.connect_db()

    def heappush(self, item):
        # Insert item into custom heap.
        self.tasks.append(item)
        self._heapify_up(len(self.tasks) - 1)

    def heapify(self, tasks_list=None):
        # Build heap from current or given list
        if tasks_list is not None:
            self.tasks = tasks_list
        for i in reversed(range(len(self.tasks)//2)):
            self._heapify_down(i)

    def _swap(self, i, j):
        self.tasks[i], self.tasks[j] = self.tasks[j], self.tasks[i]

    def _heapify_up(self, index):
        # Move element up to maintain heap order.
        while index > 0:
            parent = (index - 1) // 2
            if self.tasks[index][0] > self.tasks[parent][0]:  # compare neg priorities
                self._swap(index, parent)
                index = parent
            else:
                break

    def _heapify_down(self, index):
        # Move element down to maintain heap order.
        size = len(self.tasks)
        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            largest = index

            if left < size and self.tasks[left][0] > self.tasks[largest][0]:
                largest = left
            if right < size and self.tasks[right][0] > self.tasks[largest][0]:
                largest = right

            if largest != index:
                self._swap(index, largest)
                index = largest
            else:
                break

    # connect to db
    def connect_db(self):
        try:
            self.conn = pyodbc.connect(
                r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
                fr"DBQ={self.db_path};"
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            print("DB Connection Error:", e)

    # add task to the queue
    def add_task(self, name, time, frequency, priority, desc=""):
        if not name.strip() or not desc.strip():
            return False

        count = next(self.counter)  # tie-breaker for same priority
        self.heappush((-priority, count, time, name, frequency, desc, self.current_patient_id))
        return True

    # remove task from the queue    
    def remove_task(self, name, time, frequency, priority, desc=""):
        # find matching task ignoring the counter
        for i, task in enumerate(self.tasks):
            if (task[2] == time and task[3] == name and task[4] == frequency
                    and task[5] == desc and task[6] == self.current_patient_id):
                self.tasks.pop(i)
                self.heapify(self.tasks)

                if True:
                    QMessageBox.information(None, "Removed", f"Task ' {name}' removed successfully.")
                return True
        
        if False:
            QMessageBox.warning(None, "Not Found", f"No task found with name '{name}'")

        return False

    # load tasks from db for a specific patient
    def load_tasks_by_patient(self, patient_id):
        if not self.cursor:
            return

        self.tasks.clear()
        self.current_patient_id = patient_id

        try:
            self.cursor.execute(
                "SELECT Task_Name, Task_Time, Task_Frequency, Task_Priority, Task_Description "
                "FROM Task WHERE P_ID = ?",
                (patient_id,)
            )
            rows = self.cursor.fetchall()

            for name, time, frequency, priority, desc in rows:
                try:
                    priority = int(priority)
                except:
                    priority = 0

                if isinstance(time, str):
                    try:
                        time = datetime.fromisoformat(time)
                    except:
                        time = datetime.now()

                count = next(self.counter)
                self.heappush((-priority, count, time, name, frequency, desc, patient_id))

        except Exception as e:
            print("DB Load Error:", e)

    # get all tasks in sorted order based on priority then time
    def get_all_tasks(self):
        return sorted(self.tasks, key=lambda x: (x[0], x[1]))

    # save tasks to db
    def save_tasks_to_db(self):
        if not self.cursor or not self.current_patient_id:
            return

        try:
            self.cursor.execute("DELETE FROM Task WHERE P_ID = ?", (self.current_patient_id,))

            for neg_priority, count, time, name, frequency, desc, pid in self.tasks:
                priority = -neg_priority
                time_str = time.strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute(
                    "INSERT INTO Task (Task_Name, Task_Time, Task_Frequency, Task_Priority, Task_Description, P_ID) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (name, time_str, frequency, priority, desc, pid)
                )

            self.conn.commit()

        except Exception as e:
            print("DB Save Error:", e)

    # get filtered tasks based on time
    def get_filtered_tasks(self, filter_type="All"):
        self.update_task_times()
        now = datetime.now()
        filtered_tasks = []

        for neg_priority, count, time, name, frequency, desc, pid in self.tasks:
            include = True
            if filter_type == "Today":
                include = (time.date() == now.date())
            elif filter_type == "Weekly":
                include = (0 <= (time.date() - now.date()).days < 7)
            elif filter_type == "Monthly":
                include = (time.year == now.year and time.month == now.month)

            if include:
                filtered_tasks.append((neg_priority, count, time, name, frequency, desc, pid))

        return filtered_tasks

    # update task times based on frequency in the queue
    def update_task_times(self):
        now = datetime.now()
        updated_tasks = []

        for neg_priority, count, time, name, frequency, desc, pid in self.tasks:
            new_time = time
            while new_time < now:
                if frequency == "Daily":
                    new_time += timedelta(days=1)
                elif frequency == "Alternate Day":
                    new_time += timedelta(days=2)
                elif frequency == "Weekly":
                    new_time += timedelta(weeks=1)
                else:
                    break
            updated_tasks.append((neg_priority, count, new_time, name, frequency, desc, pid))

        self.tasks = updated_tasks
