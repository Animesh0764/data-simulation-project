import simpy
import random
import statistics
from tkinter import *
import tkinter as tk
from PIL import ImageTk, Image

# Constants
SIM_TIME = 100  # Minutes
NUM_DOCTORS = 4
TREATMENT_TIMES = {'emergency': 20, 'urgent': 10, 'non-urgent': 15}
ARRIVAL_RATE = 1
TRIAGE_LEVELS = {'emergency': 1, 'urgent': 2, 'non-urgent': 3}
PATIENTS = []

# Define a Patient class
class Patient:
    def __init__(self, id, name, age, arrival_time, triage_level, treatment_time, wait_time, sex):
        self.id = id
        self.name = name
        self.age = age
        self.arrival_time = arrival_time
        self.triage_level = triage_level
        self.treatment_time = treatment_time
        self.wait_time = wait_time
        self.sex = sex

    def info(self, time, i):
        if i == 1:
            self.got_doctor = time
        if i == 2:
            self.free_doctor = time

# Generate patients
def patient_generator(env, arrival_rate, triage_levels, treatment_times, doctors, doctor_resource):
    i = 0
    while True:
        i += 1
        yield env.timeout(random.expovariate(1 / 5))
        arrival_time = env.now
        # Output arrival information
        output_text.insert(END, f"Patient {i} arrived at the hospital at: {int(env.now)} minutes.\n")
        triage_level = random.choices(list(triage_levels.keys()), weights=[0.2, 0.3, 0.5], k=1)[0]
        treatment_time = treatment_times[triage_level]
        wait_time = 0
        # Randomly assign age and sex
        age = int(random.gauss(45, 15))
        sex = random.choice(['Male', 'Female'])
        # Creating a patient object
        patient = Patient(i, f"Patient {i}", age, arrival_time, triage_level, treatment_time, wait_time, sex)
        PATIENTS.append(patient)
        # Start patient flow
        env.process(patient_flow(env, patient, triage_levels, treatment_times, doctors, doctor_resource))
        inter_arrival_time = random.expovariate(arrival_rate)
        yield env.timeout(inter_arrival_time)

# Simulate patient flow
def patient_flow(env, patient, triage_levels, treatment_times, doctors, doctor_resource):
    with waiting_room.request() as req:
        start_wait = env.now
        yield req
        end_wait = env.now
        patient.wait_time = end_wait - start_wait
        triage_start_time = env.now
        triage_duration = random.uniform(1, 5)
        yield env.timeout(triage_duration)
        triage_end_time = env.now
        patient.triage_time = triage_end_time - triage_start_time
        if patient.triage_level == 'emergency':
            with emergency_room.request() as req:
                treatment_start_time = env.now
                yield req
                with doctor_resource.request(priority=0) as doctor_req:
                    yield doctor_req
                    patient.info(env.now, 1)
                    output_text.insert(END, f"Patient {patient.id} with an emergency got a doctor at: {int(env.now)} minutes.\n", 'emergency')  # Using 'emergency' tag
                    yield env.timeout(TREATMENT_TIMES['emergency'])
                treatment_end_time = env.now
                patient.info(env.now, 1)
                patient.treatment_time = treatment_end_time - treatment_start_time
                patient.total_time = patient.wait_time + patient.triage_time + patient.treatment_time
        elif patient.triage_level == 'urgent':
            with urgent_room.request() as req:
                treatment_start_time = env.now
                yield req
                with doctor_resource.request(priority=1) as doctor_req:
                    yield doctor_req
                    output_text.insert(END, f"Patient {patient.id} with an urgent case got a doctor at: {int(env.now)} minutes.\n", 'urgent')  # Using 'urgent' tag
                    yield env.timeout(TREATMENT_TIMES[patient.triage_level])
                treatment_end_time = env.now
                patient.treatment_time = treatment_end_time - treatment_start_time
                patient.total_time = patient.wait_time + patient.triage_time + patient.treatment_time
        else:
            with urgent_room.request() as req:
                treatment_start_time = env.now
                yield req
                with doctor_resource.request(priority=1) as doctor_req:
                    yield doctor_req
                    output_text.insert(END, f"Patient {patient.id} without emergency or urgency got a doctor at: {int(env.now)} minutes.\n", 'normal')  # Using 'normal' tag
                    yield env.timeout(TREATMENT_TIMES[patient.triage_level])
                treatment_end_time = env.now
                patient.treatment_time = treatment_end_time - treatment_start_time
                patient.total_time = patient.wait_time + patient.triage_time + patient.treatment_time

# Function to run simulation
def run_simulation():
    doctor_resource = simpy.PriorityResource(env, capacity=NUM_DOCTORS)
    doctors = []
    for i in range(NUM_DOCTORS):
        doctors.append(f"Doctor {i + 1}")

    env.process(patient_generator(env, ARRIVAL_RATE, TRIAGE_LEVELS, TREATMENT_TIMES, doctors, doctor_resource))
    env.run(until=SIM_TIME)

# Function to show patient information
def show_patient_info():
    newWindow = Toplevel(root)
    newWindow.title("Patient's Information")
    newWindow.geometry("1366x768")
    newWindow['background'] = '#121212'  # Dark background color
    newWindow.attributes("-fullscreen", True)
    image1 = Image.open("patients.png")
    image1 = image1.resize((600, 350))
    img = ImageTk.PhotoImage(image1)
    label4 = Label(newWindow, image=img, bg='#121212')  # Dark background color for image
    label4.place(x=50, y=50)
    output_text1 = Text(newWindow, height=300, bg='#121212', fg='white',  font=("Arial", 14))  # Dark background color for text, white text color
    scroll_bar = tk.Scrollbar(newWindow)
    scroll_bar.pack(side=tk.LEFT)
    output_text1.pack(side=tk.RIGHT)
    output_text1.insert(END, f"Average wait time: {int(statistics.mean([patient.wait_time for patient in PATIENTS]))} minutes.\n")
    output_text1.insert(END, f"Average treatment time: {int(statistics.mean([patient.treatment_time for patient in PATIENTS]))} minutes.\n")
    output_text1.insert(END, f"\nPatient Information:\n")
    for patient in PATIENTS:
        output_text1.insert(END, f"ID: {patient.id}\n")
        output_text1.insert(END, f"Name: {patient.name}\n")
        output_text1.insert(END, f"Age: {patient.age}\n")
        output_text1.insert(END, f"Arrival Time: {int(patient.arrival_time)} minutes\n")
        output_text1.insert(END, f"Triage Level: {patient.triage_level}\n")
        output_text1.insert(END, f"Treatment Time: {int(patient.treatment_time)} minutes\n")
        output_text1.insert(END, f"Sex: {patient.sex}\n\n")
    label5 = Label(newWindow, text="Click below to exit", bg='#121212', fg='white', font=("Arial", 14))  # Dark background color for label, white text color
    label5.place(x=280, y=500)
    b4 = Button(newWindow, text="Exit", command=newWindow.destroy, bg='#404040', fg='white', font=("Arial", 12))  # Dark button color, white text color
    b4.place(x=320, y=530)
    newWindow.mainloop()

# GUI setup
root = tk.Tk()
root.title('Hospital Emergency Room Simulation')
root.geometry("1366x768")
root['background'] = '#121212'  # Dark background color
root.attributes("-fullscreen", True)

# Initialize SimPy environment
env = simpy.Environment()
waiting_room = simpy.Resource(env, capacity=10)
urgent_room = simpy.Resource(env, capacity=3)
emergency_room = simpy.Resource(env, capacity=1)

# Load images
image = Image.open("reception.png")
image = image.resize((600, 350))
img = ImageTk.PhotoImage(image)
label = Label(root, image=img, bg='#121212')  # Dark background color for image
label.place(x=50, y=50)
output_text = Text(root, width=600, height=300, bg='#121212', fg='white',  font=("Arial", 14))  # Dark background color for text, white text color
output_text.place(x=700, y=50)

# Buttons and labels
label1 = Label(root, text="Click below to run the simulation", font=("Arial", 14), bg='#121212', fg='white')  # Change font to Arial
label1.place(x=270, y=445)

b1 = Button(root, text='Run Simulation', command=run_simulation, bg='#404040', fg='white', font=("Arial", 12))  # Change font to Arial, adjust font size
b1.place(x=310, y=480)  # Adjust vertical position for proper padding

label2 = Label(root, text="Click below to view Patient's Information", font=("Arial", 14), bg='#121212', fg='white')  # Change font to Arial
label2.place(x=220, y=525)

b2 = Button(root, text="Patient's Info", command=show_patient_info, bg='#404040', fg='white', font=("Arial", 12))  # Change font to Arial, adjust font size
b2.place(x=310, y=560)  # Adjust vertical position for proper padding

label6 = Label(root, text="Click below to exit", font=("Arial", 14), bg='#121212', fg='white')  # Change font to Arial
label6.place(x=305, y=615)

b3 = Button(root, text='Exit', command=root.destroy, bg='#404040', fg='white', font=("Arial", 12))  # Change font to Arial, adjust font size
b3.place(x=340, y=650)  # Adjust vertical position for proper padding

root.mainloop()
