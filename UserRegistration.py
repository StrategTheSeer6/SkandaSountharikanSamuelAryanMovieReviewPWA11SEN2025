import pyodbc
import bcrypt
import datetime
import re

db_path = r"SoftwareTerm4Y11PWA/PWAProjectSkandaSountharikanSamuelAryan.accdb"

conn_str = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    fr"Dbq={db_path};"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

badWords = ["Sountharikan", "Sounth"]



def is_username_valid(username):
    if len(username) > 16:
        print("Username must be 16 characters or less.")
        return False
    if any(word.lower() in username.lower() for word in badWords):
        print("Username contains inappropriate words.")
        return False
    cursor.execute("SELECT COUNT(*) FROM AccountsDetail WHERE Username=?", (username,))
    if cursor.fetchone()[0] > 0:
        print("Username already exists. Choose a different one.")
        return False
    return True

def is_password_valid(password):
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return False
    return True

def is_email_valid(email):
    # very simple regex for email validation
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, email):
        print("Invalid email format.")
        return False
    cursor.execute("SELECT COUNT(*) FROM AccountsDetail WHERE UserEmail=?", (email,))
    if cursor.fetchone()[0] > 0:
        print("Email already registered. Use a different email.")
        return False
    return True


def registerUser():
    while True:
        email = input("Enter your email: ")
        if is_email_valid(email):
            break

    while True:
        username = input("Enter your username: ")
        if is_username_valid(username):
            break

    while True:
        password = input("Enter your password: ")
        if is_password_valid(password):
            password_again = input("Enter your password again: ")
            if password != password_again:
                print("Passwords do not match.")
            else:
                break

    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    register_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pfp_default = 1
    reviev_count_default = 0
    title_default = "New User"
    bio_default = "This user doesn't have a bio yet."

    query = """
    INSERT INTO AccountsDetail
    (Username, UserPassword, UserEmail, UserPFP, UserJoinDate, UserReviewCount, UserTitle, UserDescription)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(query, (username, hashed_password.decode('utf-8'), email, pfp_default, register_date, reviev_count_default, title_default, bio_default))
    conn.commit()
    print("User registered successfully.")



def dump_accounts():
    cursor.execute("SELECT * FROM AccountsDetail")
    rows = cursor.fetchall()
    for row in rows:
        print(row)



def loginUser():
    username_or_email = input("Enter your username or email: ")
    password_entered = input("Enter your password: ")

    cursor.execute(
        "SELECT UserPassword FROM AccountsDetail WHERE Username=? OR UserEmail=?",
        (username_or_email, username_or_email)
    )
    result = cursor.fetchone()

    if result is None:
        print("No such user found.")
        return False

    hashed_pw_db = result[0].encode('utf-8')
    if bcrypt.checkpw(password_entered.encode('utf-8'), hashed_pw_db):
        print("Login successful!")
        return True
    else:
        print("Incorrect password.")
        return False



if __name__ == "__main__":
    while True:
        print("\n1. Register\n2. Login\n3. Dump\n4. Exit")
        choice = input("Choose an option: ")
        if choice == "1":
            registerUser()
        elif choice == "2":
            loginUser()
        elif choice == "3":
            dump_accounts()
        elif choice == "4":
            break
        else:
            print("Invalid option.")