-- ═══════════════════════════════════════════════════════
-- DDL — Carefree Database
-- Run once in SQL*Plus: @D:\carefree\sql\ddl.sql
-- ═══════════════════════════════════════════════════════

-- ── 1. Caretaker (no dependencies) ───────────────────
CREATE TABLE Caretaker (
    CaretakerID         VARCHAR2(20)    PRIMARY KEY,
    Caretaker_Name      VARCHAR2(100)   NOT NULL,
    Caretaker_Age       NUMBER(3),
    Caretaker_Password  VARCHAR2(50)    NOT NULL,
    Caretaker_Gender    VARCHAR2(10),
    Caretaker_Contact   VARCHAR2(20),
    Experience_Years    NUMBER(2),
    Qualification       VARCHAR2(100)
);

-- ── 2. CaretakerSkill (depends on Caretaker) ───────── 
CREATE TABLE CaretakerSkill (
    CaretakerID     VARCHAR2(20)    REFERENCES Caretaker(CaretakerID),
    Skill           VARCHAR2(100)   NOT NULL,
    CONSTRAINT pk_caretaker_skill PRIMARY KEY (CaretakerID, Skill)
);

-- ── 3. Patient (depends on Caretaker) ────────────────
CREATE TABLE Patient (
    PatientID       VARCHAR2(20)    PRIMARY KEY,
    Patient_Name    VARCHAR2(100)   NOT NULL,
    Age             NUMBER(3),
    Gender          VARCHAR2(10),
    Height          NUMBER(5,2),
    Weight          NUMBER(5,2),
    Smoker          VARCHAR2(3),
    Children        NUMBER(2),
    Region          VARCHAR2(50),
    Picture         VARCHAR2(255),
    Balance         NUMBER(10,2)    DEFAULT 0,
    Charges         NUMBER(10,2)    DEFAULT 0,
    CaretakerID     VARCHAR2(20)    REFERENCES Caretaker(CaretakerID)
);

-- ── 4. Guardian (depends on Patient) ─────────────────
CREATE TABLE Guardian (
    GuardianID              VARCHAR2(20)    PRIMARY KEY,
    Guardian_Name           VARCHAR2(100)   NOT NULL,
    Guardian_Password       VARCHAR2(50)    NOT NULL,
    Guardian_Contact        VARCHAR2(20),
    Guardian_Comment        VARCHAR2(500),
    Relation_with_patient   VARCHAR2(50),
    PatientID               VARCHAR2(20)    UNIQUE
                            REFERENCES Patient(PatientID)
);

-- ── 5. Doctor (no dependencies) ──────────────────────
CREATE TABLE Doctor (
    DoctorID        VARCHAR2(20)    PRIMARY KEY,
    Doctor_Name     VARCHAR2(100)   NOT NULL,
    Specialization  VARCHAR2(100)
);

-- ── 6. Task (depends on Patient, Caretaker) ──────────
CREATE TABLE Task (
    TaskID              NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Task_Name           VARCHAR2(100)   NOT NULL,
    Task_Time           TIMESTAMP,
    Task_Frequency      VARCHAR2(20),
    Task_Priority       VARCHAR2(10),
    Task_Description    VARCHAR2(500),
    Progress            VARCHAR2(20)    DEFAULT 'Pending',
    PatientID           VARCHAR2(20)    REFERENCES Patient(PatientID),
    CaretakerID         VARCHAR2(20)    REFERENCES Caretaker(CaretakerID)
);

-- ── 7. Appointment (depends on Patient, Doctor) ───────
CREATE TABLE Appointment (
    AppointmentID           NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Appointment_Category    VARCHAR2(50),
    Appointment_DateTime    TIMESTAMP,
    Appointment_Description VARCHAR2(500),
    Status                  VARCHAR2(20)    DEFAULT 'Scheduled',
    PatientID               VARCHAR2(20)    REFERENCES Patient(PatientID),
    DoctorID                VARCHAR2(20)    REFERENCES Doctor(DoctorID)
);

-- ── 8. Notification (depends on Caretaker, Task, Appointment) ──
CREATE TABLE Notification (
    NotificationID    NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Notif_Time        TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    Notif_Name        VARCHAR2(100),
    Message           VARCHAR2(200),
    Notif_Description VARCHAR2(500),
    Is_Sent           NUMBER(1)       DEFAULT 0,
    CaretakerID       VARCHAR2(20)    REFERENCES Caretaker(CaretakerID),
    TaskID            NUMBER          REFERENCES Task(TaskID) ON DELETE CASCADE,
    AppointmentID     NUMBER          REFERENCES Appointment(AppointmentID) ON DELETE CASCADE
);

-- ── 9. Expense (depends on Patient) ──────────────────
CREATE TABLE Expense (
    ExpenseID           VARCHAR2(20)    PRIMARY KEY,
    Expense_Name        VARCHAR2(100)   NOT NULL,
    Expense_Category    VARCHAR2(50),
    Expense_Amount      NUMBER(10,2)    NOT NULL,
    Expense_Time        TIMESTAMP,
    PatientID           VARCHAR2(20)    REFERENCES Patient(PatientID)
);

-- ── 10. Vitals (depends on Patient) ──────────────────
CREATE TABLE Vitals (
    VitalsID        NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Recorded_Time   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    VitalsCategory  VARCHAR2(50),
    PatientID       VARCHAR2(20)    REFERENCES Patient(PatientID)
);

-- ── 11. CardiacVitals (depends on Vitals) ────────────
CREATE TABLE CardiacVitals (
    VitalsID        NUMBER          PRIMARY KEY
                    REFERENCES Vitals(VitalsID),
    Pulse_Rate      NUMBER(5,2),
    Blood_Pressure  NUMBER(5,2)
);

-- ── 12. RespiratoryVitals (depends on Vitals) ────────
CREATE TABLE RespiratoryVitals (
    VitalsID            NUMBER          PRIMARY KEY
                        REFERENCES Vitals(VitalsID),
    Respiratory_Rate    NUMBER(5,2),
    Oxygen_Sat          NUMBER(5,2)
);

-- ── 13. OtherVitals (depends on Vitals) ──────────────
CREATE TABLE OtherVitals (
    VitalsID        NUMBER          PRIMARY KEY
                    REFERENCES Vitals(VitalsID),
    Blood_Glucose   NUMBER(6,2)
);

-- ── 14. Symptom (depends on Patient) ─────────────────
CREATE TABLE SymptomMaster (
    SymptomID       VARCHAR2(20)    PRIMARY KEY,
    Name            VARCHAR2(100)   NOT NULL,
    Type            VARCHAR2(50),
    Description     VARCHAR2(500),
    Severity        VARCHAR2(20)
);

-- ── 15. PatientSymptom (depends on Patient) ────────────
CREATE TABLE PatientSymptom (
    PatientID       VARCHAR2(20)    REFERENCES Patient(PatientID),
    SymptomID       VARCHAR2(20)    REFERENCES SymptomMaster(SymptomID),
    Recorded_Date   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT   pk_patient_symptom PRIMARY KEY (PatientID, SymptomID, Recorded_Date)
);

-- ── 16. CustomSymptom (depends on Patient) ────────────
CREATE TABLE CustomSymptom (
    CustomSymptomID NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Name            VARCHAR2(100)   NOT NULL,
    Type            VARCHAR2(50),
    Description     VARCHAR2(500),
    Severity        VARCHAR2(20),
    Recorded_Date   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    PatientID       VARCHAR2(20)    REFERENCES Patient(PatientID)
);

-- ═══════════════════════════════════════════════════════
-- DML — Carefree Database
-- ═══════════════════════════════════════════════════════

-- ── Seed SymptomMaster (generic hardcoded symptoms) ──
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-001', 'Fever', 'General', 'Elevated body temperature', 'Moderate');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-002', 'Headache', 'Neurological', 'Pain in the head or neck', 'Mild');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-003', 'Fatigue', 'General', 'Extreme tiredness', 'Mild');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-004', 'Chest Pain', 'Cardiac', 'Pain or pressure in chest', 'High');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-005', 'Shortness of Breath', 'Respiratory', 'Difficulty breathing', 'High');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-006', 'Nausea', 'Gastro', 'Urge to vomit', 'Mild');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-007', 'Dizziness', 'Neurological', 'Feeling faint or unsteady', 'Moderate');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-008', 'Joint Pain', 'Musculoskeletal', 'Pain in joints', 'Moderate');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-009', 'High Blood Pressure', 'Cardiac', 'Elevated BP readings', 'High');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-010', 'Swelling', 'General', 'Fluid buildup in tissues', 'Moderate');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-011', 'Cough', 'Respiratory', 'Persistent coughing', 'Mild');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-012', 'Loss of Appetite', 'Gastro', 'Reduced desire to eat', 'Mild');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-013', 'Confusion', 'Neurological', 'Disorientation or memory loss', 'High');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-014', 'Insomnia', 'General', 'Difficulty sleeping', 'Mild');
INSERT INTO SymptomMaster (SymptomID, Name, Type, Description, Severity) VALUES ('S-015', 'Back Pain', 'Musculoskeletal', 'Pain in lower or upper back', 'Moderate');

COMMIT;