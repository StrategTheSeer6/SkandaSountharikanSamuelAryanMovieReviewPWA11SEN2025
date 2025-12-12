import sqlite3
import bcrypt
import datetime
import re


conn = sqlite3.connect("PWAFramesDatabase.db")
cursor = conn.cursor()

current_user = None
current_user_level = None

#GET RID OF THIS WHEN YOU CONNECT THE API
badWords = ["Sountharikan", "Sounth"]

def is_username_valid(username):
    if len(username) > 16:
        print("Username must be 16 characters or less.")
        return False
    #CHANGE THIS PART TO THE BAD WORD API WHATEVER YOU FIND
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

    pfp_default = "default.png"
    review_count_default = 0
    title_default = "New User"
    bio_default = "This user doesn't have a bio yet."

    cursor.execute("""
        INSERT INTO AccountsDetail
        (Username, UserPassword, UserEmail, UserPFP, UserJoinDate, UserReviewCount, UserTitle, UserDescription)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, hashed_password.decode('utf-8'), email, pfp_default, register_date, review_count_default, title_default, bio_default))

    conn.commit()
    print("User registered successfully!")


def loginUser():
    global current_user, current_user_level

    username_or_email = input("Enter your username or email: ")
    password_entered = input("Enter your password: ")

    cursor.execute(
        "SELECT UserID, Username, UserPassword, UserAuthorityLevel FROM AccountsDetail WHERE Username=? OR UserEmail=?",
        (username_or_email, username_or_email)
    )
    result = cursor.fetchone()

    if result is None:
        print("No such user found.")
        return None

    user_id, username, hashed_pw, authority_level = result

    if bcrypt.checkpw(password_entered.encode('utf-8'), hashed_pw.encode('utf-8')):
        print("Login successful!")

        current_user = {
            "id": user_id,
            "username": username,
            "authority": authority_level
        }
        current_user_level = authority_level
        return current_user

    else:
        print("Incorrect password.")
        return None


def deleteUser():
    username_or_email = input("Enter your username or email to delete: ")
    password = input("Enter your password: ")

    cursor.execute(
        "SELECT UserPassword FROM AccountsDetail WHERE Username=? OR UserEmail=?",
        (username_or_email, username_or_email)
    )
    result = cursor.fetchone()
    if not result:
        print("No such user.")
        return

    hashed_pw_db = result[0].encode('utf-8')
    if bcrypt.checkpw(password.encode('utf-8'), hashed_pw_db):
        cursor.execute(
            "DELETE FROM AccountsDetail WHERE Username=? OR UserEmail=?",
            (username_or_email, username_or_email)
        )
        conn.commit()
        print("Account deleted successfully.")
    else:
        print("Incorrect password.")

def dump_accounts():
    cursor.execute("SELECT * FROM AccountsDetail")
    rows = cursor.fetchall()
    for row in rows:
        print(row)


def logoutUser():
    global current_user, current_user_level
    current_user = None
    current_user_level = None
    print("Logged out successfully!")


def get_user_authority(username_or_email):
    cursor.execute(
        "SELECT UserAuthorityLevel FROM AccountsDetail WHERE Username=? OR UserEmail=?",
        (username_or_email, username_or_email)
    )
    result = cursor.fetchone()
    return result[0] if result else None


def promote_user():
    global current_user, current_user_level

    target = input("Enter the username/email of the user to promote: ")
    target_level = get_user_authority(target)
    if target_level is None:
        print("User not found.")
        return
    if target == current_user["username"]:
        print("You cannot promote yourself.")
        return

    if current_user_level == 2:
        if target_level >= 2:
            print("You cannot promote another moderator or admin.")
            return
        if target_level == 1:
            new_level = 2
        elif target_level == 0:
            new_level = 1
        else:
            print("Invalid promotion.")
            return
    elif current_user_level == 3:
        if target_level == 3:
            print("Admins cannot change another admin's level.")
            return
        new_level = target_level + 1
    else:
        print("You don't have permission to promote users.")
        return

    cursor.execute(
        "UPDATE AccountsDetail SET UserAuthorityLevel=? WHERE Username=? OR UserEmail=?",
        (new_level, target, target)
    )
    conn.commit()
    print(f"{target} has been promoted to level {new_level}! What a good boy.")


def demote_user():
    global current_user, current_user_level

    target = input("Enter the username/email of the user to demote: ")
    target_level = get_user_authority(target)
    if target_level is None:
        print("User not found.")
        return
    if target == current_user["username"]:
        print("You cannot demote yourself.")
        return

    if current_user_level == 2:
        if target_level >= 2:
            print("You cannot demote another moderator or admin.")
            return
        new_level = target_level - 1
        if new_level < 0:
            new_level = 0
    elif current_user_level == 3:
        if target_level == 3:
            print("Admins cannot demote other admins.")
            return
        new_level = target_level - 1
        if new_level < 0:
            new_level = 0
    else:
        print("You don't have permission to demote users.")
        return

    cursor.execute(
        "UPDATE AccountsDetail SET UserAuthorityLevel=? WHERE Username=? OR UserEmail=?",
        (new_level, target, target)
    )
    conn.commit()
    print(f"{target} has been demoted to level {new_level}. Such a bad boy.")



def contains_bad_words(text):
    return any(word.lower() in text.lower() for word in badWords)


def add_comment(user_id):
    print("\n=== Add a Comment ===")

    movie_id = 1  #placeholder, cuz movie database not implemented yet. Lets just say this movie ID is for One Piece Film Red lmao

    while True:
        try:
            raw = input("Enter your rating (0–10, one decimal allowed): ").strip()

            rating = float(raw)
            if not (0 <= rating <= 10):
               print("Rating must be between 0 and 10.")
               continue
            rating = round(rating * 10) / 10.0

            break

        except ValueError:
            print("Please enter a valid number.")

    while True:
        comment_text = input("Write your comment: ").strip()
        if contains_bad_words(comment_text):
            print("Your comment contains inappropriate words. Try again.")
        elif comment_text == "":
            print("Comment cannot be empty.")
        else:
            break
    comment_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO CommentList
        (UserID, CommentTime, MovieID, CommentRating, CommentContents)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, comment_time, movie_id, rating, comment_text)
    )
    conn.commit()

    cursor.execute(
        "UPDATE AccountsDetail SET UserReviewCount = UserReviewCount + 1 WHERE UserID=?",
        (user_id,)
    )
    conn.commit()
    update_user_title(cursor, conn, user_id)
    print("Comment added successfully!")


def delete_comment():
    try:
        comment_id = int(input("Enter CommentID to delete: "))
    except ValueError:
        print("Invalid CommentID.")
        return

    cursor.execute("SELECT CommentID FROM CommentList WHERE CommentID=?", (comment_id,))
    result = cursor.fetchone()

    if not result:
        print("No comment found with that ID.")
        return
    confirm = input(f"Are you sure you want to delete CommentID {comment_id}? (y/n): ").lower()
    if confirm != "y":
        print("Deletion cancelled.")
        return

    cursor.execute("DELETE FROM CommentList WHERE CommentID=?", (comment_id,))
    conn.commit()
    print(f"Comment {comment_id} has been deleted successfully.")


def report_user():
    global current_user, current_user_level
    
    target = input("Enter the username/email of the user you want to report: ")

    cursor.execute(
        "SELECT UserID, Reported FROM AccountsDetail WHERE Username=? OR UserEmail=?",
        (target, target)
    )
    result = cursor.fetchone()

    if not result:
        print("No such user found.")
        return
    target_id, reported_status = result

    if target_id == current_user["id"]:
        print("You cannot report yourself, goofy.")
        return

    reason = input("Enter the reason for reporting this user: ")

    cursor.execute(
        "UPDATE AccountsDetail SET Reported = 1, ReportReasons=? WHERE UserID=?",
        (reason, target_id,)
    )
    conn.commit()
    print(f"{target} has been reported. A moderator will look at this soon.")


def flag_comment():
    try:
        comment_id = int(input("Enter the CommentID you want to report: "))
    except ValueError:
        print("Invalid ID.")
        return

    cursor.execute("SELECT Flagged FROM CommentList WHERE CommentID=?", (comment_id,))
    result = cursor.fetchone()
    if not result:
        print("Comment not found.")
        return

    cursor.execute(
        "UPDATE CommentList SET Flagged=1 WHERE CommentID=?",
        (comment_id,)
    )
    conn.commit()
    print(f"Comment {comment_id} has been reported!")


def view_flagged_comments(cursor):
    cursor.execute("""
        SELECT CommentID, UserID, CommentText 
        FROM CommentList 
        WHERE Flagged = 1
    """)
    rows = cursor.fetchall()

    if not rows:
        print("\nNo flagged comments found.\n")
        return

    print("\n=== FLAGGED COMMENTS ===\n")
    for row in rows:
        comment_id, user_id, text = row
        print(f"Comment ID: {comment_id}")
        print(f"Posted by User: {user_id}")
        print(f"Comment: {text}")
        print("-----------------------")


def view_reported_users(cursor):
    cursor.execute("""
        SELECT UserID, Username, UserEmail, UserAuthorityLevel, ReportReasons 
        FROM AccountsDetail 
        WHERE Reported = 1
    """)
    rows = cursor.fetchall()

    if not rows:
        print("\nNo flagged users found.\n")
        return

    print("\nREPORTED USERS\n")
    for row in rows:
        user_id, username, email, tier, reasons = row
        print(f"User ID: {user_id}")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Tier: {tier}")
        print(f"Reported For: {reasons}")
        print("-----------------------")


def view_statistics(cursor, user_id=None, username_or_email=None):
    if user_id:
        cursor.execute("SELECT UserID, Username, UserPFP, UserJoinDate, UserReviewCount, UserTitle, UserDescription FROM AccountsDetail WHERE UserID=?", (user_id,))
    elif username_or_email:
        cursor.execute("SELECT UserID, Username, UserPFP, UserJoinDate, UserReviewCount, UserTitle, UserDescription FROM AccountsDetail WHERE Username=? OR UserEmail=?", (username_or_email, username_or_email))
    else:
        print("No user specified.")
        return

    result = cursor.fetchone()
    if not result:
        print("User not found.")
        return
    uid, username, pfp, join_date, review_count, title, description = result

    cursor.execute("SELECT MIN(CommentTime), MAX(CommentTime) FROM CommentList WHERE UserID=?", (uid,))
    first_last = cursor.fetchone()
    first_comment, last_comment = first_last if first_last else (None, None)

    print(f"\n=== STATISTICS FOR {username} ===")
    print(f"UserID: {uid}")
    print(f"PFP: {pfp}")
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"Joined: {join_date}")
    print(f"Number of Comments: {review_count}")
    print(f"First Comment: {first_comment}")
    print(f"Most Recent Comment: {last_comment}")
    print("==============================\n")


def edit_profile(cursor, conn, current_user):
    while True:
        print("\n=== EDIT PROFILE MENU ===")
        print("1. Change PFP")
        print("2. Change Description")
        print("3. Change Username")
        print("4. Change Password")
        print("5. View My Statistics")
        print("6. Exit Edit Profile")
        choice = input("Choose an option: ")
        uid = current_user["id"]

        if choice == "1":
            new_pfp = input("Enter new PFP number: ").strip()
            cursor.execute("UPDATE AccountsDetail SET UserPFP=? WHERE UserID=?", (new_pfp, uid))
            conn.commit()
            print("PFP updated successfully!")
        elif choice == "2":
            new_desc = input("Enter new description: ").strip()
            cursor.execute("UPDATE AccountsDetail SET UserDescription=? WHERE UserID=?", (new_desc, uid))
            conn.commit()
            print("Description updated successfully!")
        elif choice == "3":
            while True:
                new_username = input("Enter new username: ").strip()
                if len(new_username) > 16:
                    print("Username must be 16 characters or less.")
                    continue
                cursor.execute("SELECT COUNT(*) FROM AccountsDetail WHERE Username=? AND UserID<>?", (new_username, uid))
                if any(word.lower() in new_username.lower() for word in badWords):
                    print("Username contains inappropriate words.")
                    continue
                if cursor.fetchone()[0] > 0:
                    print("Username already exists. Pick a different one.")
                    continue
                break
            cursor.execute("UPDATE AccountsDetail SET Username=? WHERE UserID=?", (new_username, uid))
            conn.commit()
            current_user["username"] = new_username
            print("Username updated successfully!")
        elif choice == "4":
            current_pw = input("Enter current password: ").strip()
            cursor.execute("SELECT UserPassword FROM AccountsDetail WHERE UserID=?", (uid,))
            hashed_pw_db = cursor.fetchone()[0].encode('utf-8')
            if not bcrypt.checkpw(current_pw.encode('utf-8'), hashed_pw_db):
                print("Incorrect current password.")
                continue
            while True:
                new_pw = input("Enter new password: ").strip()
                if len(new_pw) < 8:
                    print("Password must be at least 8 characters.")
                    continue
                confirm_pw = input("Confirm new password: ").strip()
                if new_pw != confirm_pw:
                    print("Passwords do not match.")
                    continue
                break
            hashed_new_pw = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE AccountsDetail SET UserPassword=? WHERE UserID=?", (hashed_new_pw.decode('utf-8'), uid))
            conn.commit()
            print("Password updated successfully!")
        elif choice == "5":
            view_statistics(cursor, user_id=uid)
        elif choice == "6":
            print("Exiting Edit Profile.")
            break
        else:
            print("Invalid option.")


def update_user_title(cursor, conn, user_id):
    cursor.execute("SELECT UserReviewCount FROM AccountsDetail WHERE UserID=?", (user_id,))
    result = cursor.fetchone()
    if not result:
        return
    review_count = result[0]

    milestones = [
        (1, "Newbie Commenter"),
        (5, "Casual Critic"),
        (10, "Movie Enthusiast"),
        (25, "Cinephile"),
        (100, "Film Connoisseur"),
        (500, "Movie Sage"),
        (1000, "Legendary Reviewer"),
        (5000, "Cinema Master"),
        (10000, "Ultimate Critic")
    ]

    new_title = None
    for count, title in milestones:
        if review_count >= count:
            new_title = title
        else:
            break
    if new_title:
        cursor.execute("UPDATE AccountsDetail SET UserTitle=? WHERE UserID=?", (new_title, user_id))
        conn.commit()
        print(f"Your title has been updated to: {new_title}")


def menu_not_logged_in():
    print("\n MAIN MENU logged out")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    return input("Choose an option: ")

def menu_user():
    print("\n MAIN MENU logged in w 1")
    print("1. Log Out")
    print("2. Comment")
    print("3. Edit Profile")
    print("4. Delete account")
    print("5. Report comment")
    print("6. Exit")
    print("7. Report user")
    print("8. View My Statistics")
    print("9. View Statistics by username/email")
    return input("Choose an option: ")

def menu_restricted():
    print("\n MAIN MENU logged in w 0")
    print("1. Log Out")
    print("2. Delete account")
    print("3. Exit")
    print("4. Edit Profile")
    print("5. View My Statistics")
    print("6. View Statistics by username/email")
    return input("Choose an option: ")

def menu_moderator():
    print("\n MAIN MENU logged in w 2")
    print("1. Log Out")
    print("2. Comment")
    print("3. view flagged comments")
    print("4. Delete account")
    print("5. Delete comment")
    print("6. Demote account")
    print("7. Promote account")
    print("8. Exit")
    print("9. Edit profile")
    print("0. view reported accounts")
    print("Q. View My Statistics")
    print("E. View Statistics by username/email")
    return input("Choose an option: ")

def menu_admin():
    print("\n MAIN MENU logged in w 3")
    print("1. Log Out")
    print("2. Delete comment")
    print("3. Demote account")
    print("4. Promote account")
    print("5. Dump accounts")
    print("6. Exit")
    print("7. Edit profile")
    print("8. view flagged comments")
    print("9. view reported accounts")
    print("Q. View My Statistics")
    print("E. View Statistics by username/email")
    return input("Choose an option: ")





if __name__ == "__main__":
    while True:
        if current_user is None:
            choice = menu_not_logged_in()

            if choice == "1":
                registerUser()
            elif choice == "2":
                loginUser()
            elif choice == "3":
                break
            else:
                print("Invalid option.")

        else:
            if current_user_level == 0:
                choice = menu_restricted()

                if choice == "1":
                    logoutUser()
                elif choice == "2":
                    deleteUser() 
                elif choice == "3":
                    break
                elif choice == "4":
                    edit_profile(cursor, conn, current_user)
                elif choice == "5":
                    view_statistics(cursor, user_id=current_user["id"])
                elif choice == "6":
                    username_or_email = input("Enter username or email to view statistics: ")
                    view_statistics(cursor, username_or_email=username_or_email)
                else:
                    print("Invalid option.")

            elif current_user_level == 1:
                choice = menu_user()

                if choice == "1":
                    logoutUser()
                elif choice == "2":
                    add_comment(current_user["id"])
                elif choice == "3":
                    edit_profile(cursor, conn, current_user)
                elif choice == "4":
                    deleteUser()    
                elif choice == "5":
                    flag_comment()
                elif choice == "6":
                    break
                elif choice == "7":
                    report_user()
                elif choice == "8":
                    view_statistics(cursor, user_id=current_user["id"])
                elif choice == "9":
                    username_or_email = input("Enter username or email to view statistics: ")
                    view_statistics(cursor, username_or_email=username_or_email)
                else:
                    print("Not implemented yet or invalid option.")

            elif current_user_level == 2:
                choice = menu_moderator()

                if choice == "1":
                    logoutUser()
                elif choice == "2":
                    add_comment(current_user["id"])
                elif choice == "3":
                    view_flagged_comments(cursor)
                elif choice == "4":
                    deleteUser()
                elif choice == "5":
                    delete_comment()
                elif choice == "6":
                    demote_user()
                elif choice == "7":
                    promote_user()
                elif choice == "8":
                    break
                elif choice == "9":
                    edit_profile(cursor, conn, current_user)
                elif choice == "0":
                    view_reported_users(cursor)
                elif choice.upper() == "Q":
                    view_statistics(cursor, user_id=current_user["id"])
                elif choice.upper() == "E":
                    username_or_email = input("Enter username or email to view statistics: ")
                    view_statistics(cursor, username_or_email=username_or_email)
                else:
                    print("Not implemented yet or invalid option.")

            elif current_user_level == 3:
                choice = menu_admin()

                if choice == "1":
                    logoutUser()
                elif choice == "2":
                    delete_comment()
                elif choice == "3":
                    demote_user()
                elif choice == "4":
                    promote_user()
                elif choice == "5":
                    dump_accounts()
                elif choice == "6":
                    break
                elif choice == "7":
                    edit_profile(cursor, conn, current_user)
                elif choice == "8":
                    view_flagged_comments(cursor)
                elif choice == "9":
                    view_reported_users(cursor)
                elif choice.upper() == "Q":
                    view_statistics(cursor, user_id=current_user["id"])
                elif choice.upper() == "E":
                    username_or_email = input("Enter username or email to view statistics: ")
                    view_statistics(cursor, username_or_email=username_or_email)
                else:
                    print("Not implemented yet or invalid option.")


conn.close()