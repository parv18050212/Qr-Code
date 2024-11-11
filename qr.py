import cv2
from pyzbar.pyzbar import decode
import csv
import os
from datetime import datetime

# Define the CSV file for storing attendance
filename = "attendance.csv"

# Initialize attendance with all students marked as "Absent" (0)
def initialize_attendance(students_list):
    attendance = {}
    for student in students_list:
        name, reg_id = student
        attendance[reg_id] = {
            'name': name,
            'reg_id': reg_id,
            'status': 0,  # 0 for Absent
            'last_seen': None
        }
    return attendance

# Load student list from CSV file (contains name and reg_id only)
def load_student_list(filename='students.csv'):
    students = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    students.append((row[0], row[1]))  # (name, reg_id)
    return students

# Save attendance to CSV file
def save_attendance(attendance):
    with open(filename, 'w', newline='') as f:
        fieldnames = ['name', 'reg_id', 'status', 'last_seen']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in attendance.values():
            # Convert last_seen to string for CSV if not None
            if record['last_seen']:
                record['last_seen'] = record['last_seen'].isoformat()
            writer.writerow(record)

# Mark a student as "Present" (1) based on QR code scan
def mark_attendance(name, reg_id, attendance):
    current_time = datetime.now()
    if reg_id in attendance:
        attendance[reg_id]['status'] = 1  # 1 for Present
        attendance[reg_id]['last_seen'] = current_time
    else:
        print(f"Warning: {name} with reg_id {reg_id} not found in the list.")

# Initialize IP Webcam stream URL
ip_camera_url = "http://192.168.137.141:8080/video"  # Replace with your IP camera URL
cap = cv2.VideoCapture(ip_camera_url)

if not cap.isOpened():
    print("Error: Could not connect to IP camera.")
    exit()

print("QR code scanner ready. Show QR code to the IP camera...")

# Load students and initialize attendance with all marked "Absent" (0)
students_list = load_student_list()  # Load from 'students.csv'
attendance = initialize_attendance(students_list)

while True:
    _, frame = cap.read()
    decoded_objs = decode(frame)

    for obj in decoded_objs:
        data = obj.data.decode("utf-8")
        print(f"QR Code Data: {data}")

        # Parse data to extract relevant info
        try:
            details = data.split(", ")
            name = details[0].split(": ")[1]
            reg_id = details[1].split(": ")[1]
        except (IndexError, ValueError):
            print("Error: QR code data format is incorrect.")
            continue

        # Mark the person as present in the attendance dictionary
        mark_attendance(name, reg_id, attendance)
        print(f"Attendance recorded for {name} - {reg_id}")

        # Show acknowledgment for 2 seconds
        for _ in range(40):
            cv2.putText(frame, "Attendance Recorded", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Scanner", frame)
            if cv2.waitKey(50) & 0xFF == ord('q'):
                break

    # Save attendance data to CSV after each update
    save_attendance(attendance)

    # Display the camera feed
    cv2.imshow("Scanner", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
