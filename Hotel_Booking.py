import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry  # Import tkcalendar for date selection
import threading
from multiprocessing import Process, Queue
from PIL import Image, ImageTk

# Create or connect to the SQLite database
conn = sqlite3.connect('hotel_database.db')
cursor = conn.cursor()

# Create the "hotel" table if it doesn't exist with the corrected schema
cursor.execute('''  
    CREATE TABLE IF NOT EXISTS hotel (
        id INTEGER PRIMARY KEY,
        name TEXT,
        room INTEGER,
        checkin DATE,
        checkout DATE,
        price REAL,
        special_requests TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Create a lock to control access to the booking operation
booking_lock = threading.Lock()

def calculate_price(checkin, checkout):
    # Calculate the price based on the selected check-in and check-out dates
    # Add your pricing logic here (e.g., price per night, discounts)
    return 1500 * (checkout - checkin).days

def is_room_available(room, checkin, checkout):
    # Check if the room is available for the given check-in and check-out dates
    cursor.execute("SELECT id FROM hotel WHERE room = ? AND (checkin <= ? AND checkout >= ?)", (room, checkout, checkin))
    booking = cursor.fetchone()
    return booking is None

def book_room():
    name = name_entry.get()
    room = room_entry.get()
    checkin = checkin_calendar.get_date()
    checkout = checkout_calendar.get_date()
    special_requests = special_requests_entry.get("1.0", "end")

    if not name or not room:
        messagebox.showerror("Error", "Both name and room number are required.")
        return

    try:
        room = int(room)
    except ValueError:
        messagebox.showerror("Error", "Room must be a number.")
        return

    if not is_room_available(room, checkin, checkout):
        messagebox.showerror("Error", f"Room {room} is not available for the selected dates.")
        return

    price = calculate_price(checkin, checkout)

    # Acquire the lock before booking
    booking_lock.acquire()
    cursor.execute("INSERT INTO hotel (name, room, checkin, checkout, price, special_requests) VALUES (?, ?, ?, ?, ?, ?)",
                   (name, room, checkin, checkout, price, special_requests))
    conn.commit()
    # Release the lock after booking
    booking_lock.release()

    success_message = f"Room {room} booked successfully for {name}\nTotal Price: ₹{price}"
    messagebox.showinfo("Booking Successful", success_message)

    name_entry.delete(0, "end")
    room_entry.delete(0, "end")
    special_requests_entry.delete("1.0", "end")
    view_room_bookings()

def view_room_bookings():
    # Display a list of room bookings
    cursor.execute("SELECT name, room, checkin, checkout, price FROM hotel")
    bookings = cursor.fetchall()

    if not bookings:
        result_label.config(text="No room bookings found.")
    else:
        result_label.config(text="Room Bookings:\n")
        for booking in bookings:
            name, room, checkin, checkout, price = booking
            result_label.config(text=result_label.cget("text") +
                               f"Name: {name}, Room: {room}, Check-in: {checkin}, Check-out: {checkout}, Price: ₹{price}\n")

def search_booking():
    name = name_search_entry.get()
    cursor.execute("SELECT name, room, checkin, checkout, price FROM hotel WHERE name = ?", (name,))
    bookings = cursor.fetchall()

    if not bookings:
        search_result_label.config(text=f"No bookings found for {name}.")
    else:
        search_result_label.config(text="Booking(s) found:\n")
        for booking in bookings:
            name, room, checkin, checkout, price = booking
            search_result_label.config(text=search_result_label.cget("text") +
                                   f"Name: {name}, Room: {room}, Check-in: {checkin}, Check-out: {checkout}, Price: ₹{price}\n")

# def cancel_booking():
    # name = name_cancel_entry.get()
    # cursor.execute("DELETE FROM hotel WHERE name = ?", (name,))
    # conn.commit()
    # messagebox.showinfo("Booking Canceled", f"Booking(s) for {name} canceled.")
    # view_room_bookings() 

def cancel_booking():
    name = name_cancel_entry.get()
    
    if not name:
        messagebox.showerror("Error", "Please enter a name to cancel the booking.")
        return

    cursor.execute("DELETE FROM hotel WHERE name = ?", (name,))
    conn.commit()
    messagebox.showinfo("Booking Canceled", f"Booking(s) for {name} canceled.")
    view_room_bookings()

# Create the main window
root = tk.Tk()
root.title("Hotel Booking System")

# Set the size of the GUI window
window_width = 550
window_height = 800
root.geometry(f"{window_width}x{window_height}")

# Add a logo image to the GUI
logo_image = Image.open("vu.png")
logo_image = logo_image.resize((370, 90))
logo_photo = ImageTk.PhotoImage(logo_image)
logo_label = tk.Label(root, image=logo_photo)
logo_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

# Create and configure widgets
name_label = tk.Label(root, text="Enter name:")
name_entry = tk.Entry(root)
room_label = tk.Label(root, text="Enter room number:")
room_entry = tk.Entry(root)

checkin_label = tk.Label(root, text="Check-in Date:")
checkin_calendar = DateEntry(root, width=12, background="darkblue", date_pattern="dd/mm/yyyy")
checkin_calendar.set_date(datetime.now())

checkout_label = tk.Label(root, text="Check-out Date:")
checkout_calendar = DateEntry(root, width=12, background="darkblue", date_pattern="dd/mm/yyyy")
checkout_calendar.set_date(datetime.now() + timedelta(days=1))

special_requests_label = tk.Label(root, text="Special Requests:")
special_requests_entry = tk.Text(root, height=5, width=40)

book_button = tk.Button(root, text="Book Room", command=book_room)
view_button = tk.Button(root, text="View Room Bookings", command=view_room_bookings)
result_label = tk.Label(root, text="")

# Place widgets in the grid
name_label.grid(row=1, column=0, padx=10, pady=5)
name_entry.grid(row=1, column=1, padx=10, pady=5)
room_label.grid(row=2, column=0, padx=10, pady=5)
room_entry.grid(row=2, column=1, padx=10, pady=5)
checkin_label.grid(row=3, column=0, padx=10, pady=5)
checkin_calendar.grid(row=3, column=1, padx=10, pady=5)
checkout_label.grid(row=4, column=0, padx=10, pady=5)
checkout_calendar.grid(row=4, column=1, padx=10, pady=5)
special_requests_label.grid(row=5, column=0, padx=10, pady=5)
special_requests_entry.grid(row=5, column=1, padx=10, pady=5)
book_button.grid(row=6, column=0, columnspan=2, pady=10)
view_button.grid(row=7, column=0, columnspan=2, pady=10)
result_label.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

# Search and cancel booking section
search_label = tk.Label(root, text="Search Booking by Name:")
name_search_entry = tk.Entry(root)
search_button = tk.Button(root, text="Search", command=search_booking)
search_result_label = tk.Label(root, text="")

cancel_label = tk.Label(root, text="Cancel Booking by Name:")
name_cancel_entry = tk.Entry(root)
cancel_button = tk.Button(root, text="Cancel Booking", command=cancel_booking)

# Place search and cancel widgets in the grid
search_label.grid(row=9, column=0, padx=10, pady=5)
name_search_entry.grid(row=9, column=1, padx=10, pady=5)
search_button.grid(row=10, column=0, columnspan=2, pady=10)
search_result_label.grid(row=11, column=0, columnspan=2, padx=10, pady=10)

cancel_label.grid(row=12, column=0, padx=10, pady=5)
name_cancel_entry.grid(row=12, column=1, padx=10, pady=5)
cancel_button.grid(row=13, column=0, columnspan=2, pady=10)

root.mainloop()
