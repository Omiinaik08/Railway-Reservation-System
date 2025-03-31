import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect('railway.db')
c = conn.cursor()

def create_db():
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY,
                  password TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS employees
                 (employee_id INTEGER PRIMARY KEY,
                  password TEXT NOT NULL,
                  designation TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS trains
               (train_id INTEGER PRIMARY KEY,
               train_name TEXT NOT NULL,
               start_station TEXT NOT NULL,
               end_station TEXT NOT NULL)''')

# Call create_db() once to initialize the database
create_db()

def search_trains(train_id):
    train_query = c.execute("SELECT * FROM trains WHERE train_id=?", (train_id,))
    train_data = train_query.fetchone()
    return train_data

def train_destination(start_station, end_station):
    train_query = c.execute("SELECT * FROM trains WHERE start_station=? AND end_station=?", (start_station, end_station,))
    train_data = train_query.fetchone()
    return train_data

def add_train(train_id, train_name, departure_date, start_station, end_station):
    c.execute("INSERT INTO trains (train_id, train_name, departure_date, start_station, end_station) VALUES (?, ?, ?, ?, ?)",
              (train_id, train_name, departure_date, start_station, end_station))
    conn.commit()

def create_seats(train_id):
    c.execute(f"CREATE TABLE IF NOT EXISTS seats_{train_id} ("
              f"seat_number INTEGER PRIMARY KEY, "
              f"seat_type TEXT, "
              f"is_booked INTEGER, "
              f"passenger_name TEXT, "
              f"passenger_age INTEGER, "
              f"passenger_gender TEXT)")
    
    for i in range(1, 101):
        val = categoriz_seat(i)
        c.execute(f"INSERT INTO seats_{train_id} (seat_number, seat_type, is_booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)",
                  (i, val, 0, '', '', ''))
        conn.commit()

def allocate_next_available_seat(train_id, seat_type):
    seat_query = c.execute(f"SELECT seat_number FROM seats_{train_id} WHERE seat_type=? AND is_booked=0 ORDER BY seat_number ASC", (seat_type,))
    result = seat_query.fetchall()
    
    if result:
        return result[0][0]  # Return the seat number

def categoriz_seat(seat_number):
    if (seat_number % 10) in [0, 4, 5, 9]:
        return "Window"
    elif (seat_number % 10) in [2, 3, 6, 7]:
        return "Aisle"
    else:
        return "Middle"

def view_seats(train_id):
    train_query = c.execute("SELECT * FROM trains WHERE train_id=?", (train_id,))
    train_data = train_query.fetchone()
    
    if train_data:
        seat_query = c.execute(f'''SELECT seat_number, seat_type, passenger_name, passenger_age, passenger_gender, is_booked FROM seats_{train_id} ORDER BY seat_number ASC''')
        result = seat_query.fetchall()
        
        if result:
            df = pd.DataFrame(result, columns=['Seat Number', 'Seat Type', 'Passenger Name', 'Passenger Age', 'Passenger Gender', 'Is Booked'])
            st.dataframe(data=df)

def book_tickets(train_id, seat_type, passenger_name, passenger_age, passenger_gender):
    train_query = c.execute("SELECT * FROM trains WHERE train_id=?", (train_id,))
    train_data = train_query.fetchone()
    
    if train_data:
        seat_number = allocate_next_available_seat(train_id, seat_type)  
                                 
        if seat_number:
            c.execute(f"UPDATE seats_{train_id} SET is_booked=1, passenger_name=?, passenger_age=?, seat_type=?, passenger_gender=? WHERE seat_number=?",
                      (passenger_name, passenger_age, seat_type, passenger_gender, seat_number))
            conn.commit()
            st.success(f"Ticket booked successfully! Seat Number: {seat_number}")

def cancel_tickets(train_id, seat_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_id=?", (train_id,))
    train_data = train_query.fetchone() 
    
    if train_data:
        c.execute(f'''UPDATE seats_{train_id} SET is_booked=0, passenger_name='', passenger_age='', passenger_gender='' WHERE seat_number=?''', (seat_number,))
        conn.commit()
        st.success(f"Ticket cancelled successfully! Seat Number: {seat_number}")

def delete_train(train_id, departure_date):
    train_query = c.execute("SELECT * FROM trains WHERE train_id=?", (train_id,))
    train_data = train_query.fetchone()
    
    if train_data:
        c.execute("DELETE FROM trains WHERE train_id=? AND departure_date=?", (train_id, departure_date))
        conn.commit()
        st.success(f"Train deleted successfully! Train Number: {train_id}")     

def train_function():
    st.title("Train Administration")
    function = st.sidebar.selectbox("Select Train Function", ["Add Train", "View Trains", "Search Train", "Delete Train", "Book Ticket", "Cancel Ticket", "View Seats"])
    
    if function == "Add Train":
        st.header("Add Train")
        with st.form(key='new_train_details'):
            train_name = st.text_input("Train Name")
            train_id = st.text_input("Train ID")
            departure_date = st.date_input("Departure Date")
            start_station = st.text_input("Start Station")
            end_station = st.text_input("End Station")
            submitted = st.form_submit_button("Add Train")
        
        if submitted and train_name and train_id and start_station and end_station:
            add_train(train_id, train_name, departure_date, start_station, end_station)
            st.success("Train added successfully!")
    
    elif function == "View Trains":
        st.title("View all Trains")
        train_query = c.execute("SELECT * FROM trains")
        train_data = train_query.fetchall()
        st.write(train_data)
        
    elif function == "Book Ticket":
        st.title("Book Train Ticket")
        train_id = st.text_input("Enter Train ID")
        seat_type = st.selectbox("Seat Type", ["Aisle", "Middle", "Window"])
        passenger_name = st.text_input("Passenger Name")
        passenger_age = st.number_input("Passenger Age", min_value=1)
        passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female"], index=0)
     
        if st.button("Book Ticket"):
            if train_id and passenger_name and passenger_age and passenger_gender:
                book_tickets(train_id, seat_type, passenger_name, passenger_age, passenger_gender)
                
    elif function == "Cancel Ticket":
        st.title("Cancel Train Ticket")
        train_id = st.text_input("Enter Train ID")
        seat_number = st.number_input("Seat Number", min_value=1)
        
        if st.button("Cancel Ticket"):
            if train_id and seat_number:
                cancel_tickets(train_id, seat_number)
    
    elif function == "View Seats":
        st.title("View Train Seats")
        train_id = st.text_input("Enter Train ID")
        
        if st.button("Submit"):
            if train_id:
                view_seats(train_id)
    
    elif function == "Delete Train":
        st.title("Delete Train")
        train_id = st.text_input("Enter Train ID")
        departure_date = st.date_input("Departure Date")
        
        if st.button("Delete Train"):
            if train_id:
                c.execute(f"DROP TABLE IF EXISTS seats_{train_id}")
                delete_train(train_id, departure_date)

train_function()
