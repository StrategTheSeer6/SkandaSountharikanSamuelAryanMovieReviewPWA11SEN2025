import sqlite3
import bcrypt
import datetime
import re
import difflib

conn = sqlite3.connect("PWAFramesDatabase.db")
cursor = conn.cursor()

current_user = None
current_user_level = None

VALID_GENRES = {"action", "adventure", "fantasy", "romance", "comedy", "drama", "supernatural", "sci-fi", "superhero", "historical", "epic", "satire", "crime", "thriller", "horror", "spy", "music", "family", "biography", "animation", "psychological"}
VALID_CLASSIFICATIONS = {"G", "PG", "M", "MA 15+", "R 18"}
VALID_RATING_ORDERS = {"asc", "desc"}
VALID_YEAR_ORDERS = {"new_to_old", "old_to_new"}

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

    # THIS IS ONLY FOR NOW CUZ I DON'T HAVE FRONTEND, ONCE THATS DONE, THEN y'know how it goes, you comment on the movie you're on.
    cursor.execute("SELECT FilmID, FilmName FROM MovieList")
    all_movies = cursor.fetchall()
    
    while True:
        try:
            print("\nAvailable movies:")
            for movie in all_movies:
                print(f"{movie[0]}: {movie[1]}")
            
            movie_id = int(input("Enter the FilmID of the movie you want to comment on: ").strip())
            if any(movie[0] == movie_id for movie in all_movies):
                break
            else:
                print("Invalid FilmID. Please choose from the list above.")
        except ValueError:
            print("Please enter a valid number.")


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
        "SELECT FilmRating, FilmReviewCount FROM MovieList WHERE FilmID=?",
        (movie_id,)
    )
    result = cursor.fetchone()
    if result:
        old_avg, old_count = result
        if old_avg is None:
            old_avg = 0
        if old_count is None:
            old_count = 0
        new_count = old_count + 1
        new_avg = ((old_avg * old_count) + rating) / new_count
        cursor.execute(
            "UPDATE MovieList SET FilmRating=?, FilmReviewCount=? WHERE FilmID=?",
            (round(new_avg, 1), new_count, movie_id)
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

    # Fetch comment info
    cursor.execute(
        "SELECT UserID, MovieID, CommentRating FROM CommentList WHERE CommentID=?",
        (comment_id,)
    )
    comment_info = cursor.fetchone()

    if not comment_info:
        print("No comment found with that ID.")
        return

    user_id, movie_id, comment_rating = comment_info

    confirm = input(f"Are you sure you want to delete CommentID {comment_id}? (y/n): ").lower()
    if confirm != "y":
        print("Deletion cancelled.")
        return

    # Delete the comment
    cursor.execute("DELETE FROM CommentList WHERE CommentID=?", (comment_id,))
    conn.commit()

    # Update user's review count
    cursor.execute(
        "UPDATE AccountsDetail SET UserReviewCount = UserReviewCount - 1 WHERE UserID=? AND UserReviewCount > 0",
        (user_id,)
    )
    conn.commit()
    update_user_title(cursor, conn, user_id)

    # Update movie's review count and average rating
    cursor.execute(
        "SELECT FilmRating, FilmReviewCount FROM MovieList WHERE FilmID=?",
        (movie_id,)
    )
    movie_info = cursor.fetchone()
    if movie_info:
        film_rating, film_review_count = movie_info
        new_review_count = max(film_review_count - 1, 0)

        if new_review_count == 0:
            new_average = 0.0
        else:
            total_rating = film_rating * film_review_count
            total_rating -= comment_rating
            new_average = total_rating / new_review_count

        cursor.execute(
            "UPDATE MovieList SET FilmRating=?, FilmReviewCount=? WHERE FilmID=?",
            (new_average, new_review_count, movie_id)
        )
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

    print(f"\n=== STATISTICS FOR {username} ===")
    print(f"UserID: {uid}")
    print(f"PFP: {pfp}")
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"Joined: {join_date}")
    print(f"Number of Comments: {review_count}")
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


def list_all_movies():
    cursor.execute("SELECT FilmID, FilmName FROM MovieList")
    movies = cursor.fetchall()
    if not movies:
        print("No movies found in the database.")
        return
    print("\n=== All Movies ===")
    for movie_id, movie_name in movies:
        print(f"{movie_id}: {movie_name}")
    print("==================\n")


def menu_not_logged_in():
    print("\n MAIN MENU logged out")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    print("4. List all movies")
    print("5. Search movies")
    print("6. Browse movies")
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
    print("0. List all movies")
    print("B. Browse movies")
    print("S. Search movies")
    return input("Choose an option: ")

def menu_restricted():
    print("\n MAIN MENU logged in w 0")
    print("1. Log Out")
    print("2. Delete account")
    print("3. Exit")
    print("4. Edit Profile")
    print("5. View My Statistics")
    print("6. View Statistics by username/email")
    print("7. List all movies")
    print("8. Browse movies")
    print("9. Search movies")
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
    print("X. List all movies")
    print("B. Browse movies")
    print("S. Search movies")
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
    print("X. List all movies")
    print("B. Browse movies")
    print("S. Search movies")
    return input("Choose an option: ")


def genre_weight_clause():
    return """
        CASE
            WHEN FilmGenreP = ? THEN 1
            WHEN FilmGenreS = ? THEN 2
            WHEN FilmGenreT = ? THEN 3
            WHEN FilmGenreQ = ? THEN 4
            ELSE 5
        END
    """


def build_filter_conditions(filters):
    conditions = []
    params = []

    if filters.get("classification"):
        conditions.append("FilmClassification = ?")
        params.append(filters["classification"])

    return conditions, params


def build_order_by_clause(filters):
    order_parts = []
    params = []

    if filters.get("genre"):
        order_parts.append(genre_weight_clause())
        params.extend([filters["genre"]] * 4)

    # Default or secondary ordering by rating
    order_parts.append("FilmRating DESC")

    # Year sorting (optional)
    if filters.get("year_sort") == "new_to_old":
        order_parts.append("FilmReleaseDate DESC")
    elif filters.get("year_sort") == "old_to_new":
        order_parts.append("FilmReleaseDate ASC")

    return " ORDER BY " + ", ".join(order_parts), params


def browse_movies(filters=None):
    if filters is None:
        filters = {}

    query = """
        SELECT
            FilmID,
            FilmName,
            FilmGenreP,
            FilmGenreS,
            FilmGenreT,
            FilmGenreQ,
            FilmRating,
            FilmReleaseDate,
            FilmClassification
        FROM MovieList
    """

    conditions, where_params = build_filter_conditions(filters)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    order_clause, order_params = build_order_by_clause(filters)
    query += order_clause

    cursor.execute(query, where_params + order_params)
    movies = cursor.fetchall()

    if not movies:
        print("No movies found.")
        return

    print("\n=== Browse Movies ===")
    for m in movies:
        print(
            f"[{m[0]}] {m[1]} | Rating: {m[6]} | "
            f"Genres: {m[2]}, {m[3]}, {m[4]}, {m[5]} | "
            f"Year: {m[7]} | Class: {m[8]}"
        )


def search_movies(
    genre_filters=None, #options are action, adventure, fantasy, romance, comedy, drama, supernatural, sci-fi, superhero, historical, epic, satire, crime, thriller, horror, spy, music, family, biography, animation, psychological
    classification_filters=None, #options are G, PG, M, MA 15+, 
    rating_order="desc", #options are asc, desc
    year_order=None #options are new_to_old, old_to_new
):
    query = input("Search for a movie: ").strip()
    if not query:
        print("Search cannot be empty.")
        return
    
    cursor.execute(
        """
        SELECT *
        FROM MovieList
        WHERE FilmName LIKE ?
        """,
        (f"%{query}%",)
    )
    results = cursor.fetchall()

    if not results:
        cursor.execute("SELECT FilmName FROM MovieList")
        all_names = [row[0] for row in cursor.fetchall()]

        matches = difflib.get_close_matches(query, all_names, n=5, cutoff=0.6)
        if not matches:
            print("No matching or similar movies found.")
            return

        placeholders = ",".join("?" for _ in matches)
        cursor.execute(
            f"""
            SELECT *
            FROM MovieList
            WHERE FilmName IN ({placeholders})
            """,
            matches
        )
        results = cursor.fetchall()

    filtered = []
    for movie in results:
        (
            film_id,
            film_name,
            genre_p,
            genre_s,
            genre_t,
            genre_q,
            film_rating,
            review_count,
            release_date,
            classification,
            description,
            directors,
            actors,
            image_link
        ) = movie

        if genre_filters:
            genres = {genre_p, genre_s, genre_t, genre_q}
            if not genres.intersection(genre_filters):
                continue

        if classification_filters:
            if classification not in classification_filters:
                continue
        filtered.append(movie)
    if not filtered:
        print("No movies match your filters.")
        return

    if rating_order == "desc":
        filtered.sort(key=lambda m: m[6] or 0, reverse=True)
    elif rating_order == "asc":
        filtered.sort(key=lambda m: m[6] or 0)

    if year_order == "new_to_old":
        filtered.sort(key=lambda m: m[8], reverse=True)
    elif year_order == "old_to_new":
        filtered.sort(key=lambda m: m[8])

    print("\nMovies found:")
    for movie in filtered:
        print(f"[{movie[0]}] {movie[1]} ({movie[8]} | {movie[9]})")



def browse_movies_terminal():
    print("\n=== Browse Movies ===")
    print("You can leave any filter empty by pressing Enter.\n")

    while True:
        genre = input("Enter genre to prioritize: ").strip()
        if not genre:
            genre = None
            break
        if genre.lower() in VALID_GENRES:
            genre = genre.lower()
            break
        print(f"Invalid genre. Valid options: {', '.join(VALID_GENRES)}")

    while True:
        classification = input("Enter classification (G, PG, M, MA 15+, R 18): ").strip()
        if not classification:
            classification = None
            break
        if classification.upper() in VALID_CLASSIFICATIONS:
            classification = classification.upper()
            break
        print(f"Invalid classification. Valid options: {', '.join(VALID_CLASSIFICATIONS)}")

    while True:
        year_sort = input("Enter year sort order ('new_to_old' or 'old_to_new'): ").strip()
        if not year_sort:
            year_sort = None
            break
        if year_sort in VALID_YEAR_ORDERS:
            break
        print(f"Invalid option. Valid options: {', '.join(VALID_YEAR_ORDERS)}")

    filters = {}
    if genre:
        filters["genre"] = genre
    if classification:
        filters["classification"] = classification
    if year_sort:
        filters["year_sort"] = year_sort

    browse_movies(filters)


def search_movies_terminal():
    print("\n=== Search Movies ===")
    print("You can leave any filter empty by pressing Enter.\n")
    query = input("Enter movie title to search: ").strip()
    if not query:
        print("Search cannot be empty.")
        return

    while True:
        genre_input = input("Enter genres to filter by (comma-separated): ").strip()
        if not genre_input:
            genre_filters = None
            break
        genres = {g.strip().lower() for g in genre_input.split(",")}
        invalid = genres - VALID_GENRES
        if invalid:
            print(f"Invalid genres: {', '.join(invalid)}. Valid options: {', '.join(VALID_GENRES)}")
            continue
        genre_filters = genres
        break

    while True:
        classification_input = input("Enter classifications to filter by (comma-separated): ").strip()
        if not classification_input:
            classification_filters = None
            break
        classifications = {c.strip().upper() for c in classification_input.split(",")}
        invalid = classifications - VALID_CLASSIFICATIONS
        if invalid:
            print(f"Invalid classifications: {', '.join(invalid)}. Valid options: {', '.join(VALID_CLASSIFICATIONS)}")
            continue
        classification_filters = classifications
        break

    while True:
        rating_order = input("Sort by rating? 'asc' or 'desc' (default 'desc'): ").strip() or "desc"
        if rating_order in VALID_RATING_ORDERS:
            break
        print(f"Invalid option. Valid options: {', '.join(VALID_RATING_ORDERS)}")

    while True:
        year_order = input("Sort by year? 'new_to_old' or 'old_to_new' (leave empty for no sorting): ").strip()
        if not year_order:
            year_order = None
            break
        if year_order in VALID_YEAR_ORDERS:
            break
        print(f"Invalid option. Valid options: {', '.join(VALID_YEAR_ORDERS)}")

    search_movies(
        genre_filters=genre_filters,
        classification_filters=classification_filters,
        rating_order=rating_order,
        year_order=year_order
    )


def reset_database():
    # Drop old tables
    cursor.execute("DROP TABLE IF EXISTS CommentList")
    cursor.execute("DROP TABLE IF EXISTS MovieList")
    cursor.execute("DROP TABLE IF EXISTS AccountsDetail")


    # Recreate AccountsDetail
    cursor.execute("""
    CREATE TABLE AccountsDetail (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT UNIQUE NOT NULL,
        UserPassword TEXT NOT NULL,
        UserEmail TEXT UNIQUE NOT NULL,
        UserPFP INTEGER DEFAULT 0,
        UserJoinDate TEXT NOT NULL,
        UserReviewCount INTEGER DEFAULT 0,
        UserTitle TEXT DEFAULT 'New User',
        UserDescription TEXT DEFAULT 'This user does not have a bio yet.',
        UserAuthorityLevel INTEGER DEFAULT 1,
        Reported INTEGER DEFAULT 0,
        ReportReasons TEXT
    )
    """)

    # Recreate MovieList
    cursor.execute("""
    CREATE TABLE MovieList (
        FilmID INTEGER PRIMARY KEY AUTOINCREMENT,
        FilmName TEXT NOT NULL,
        FilmGenreP TEXT,
        FilmGenreS TEXT,
        FilmGenreT TEXT,
        FilmGenreQ TEXT,
        FilmRating REAL,
        FilmReviewCount INTEGER DEFAULT 0,
        FilmReleaseDate TEXT,
        FilmClassification TEXT,
        FilmDescription TEXT,
        FilmDirectors TEXT,
        FilmActors TEXT,
        FlimImageLink TEXT
    )
    """)

    # Recreate CommentList
    cursor.execute("""
    CREATE TABLE CommentList (
        CommentID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER NOT NULL,
        CommentTime TEXT NOT NULL,
        MovieID INTEGER NOT NULL,
        CommentRating REAL,
        CommentContents TEXT NOT NULL,
        Flagged INTEGER DEFAULT 0,
        FOREIGN KEY (UserID) REFERENCES AccountsDetail(UserID),
        FOREIGN KEY (MovieID) REFERENCES MovieList(FilmID)
    )
    """)

    # Insert Admin Account
    cursor.execute("""
    INSERT INTO AccountsDetail (
        Username, UserPassword, UserEmail, UserJoinDate,
        UserAuthorityLevel, UserTitle
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "TheAdmin",
        "admin194(<|>/)*#Fh8@78hf9Q@*f9aos-wQhaP2any%",
        "admin.adminson@administrator.com",
        "Long Before Time Had A Name",
        3,
        "System Overlord"
    ))

    movies = [
    (
        "Avatar: The Way of Water",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "2022",
        "M",
        "Jake Sully protects his family among the ocean clans of Pandora. Jake Sully and Ney'tiri have formed a family and are doing everything to stay together. However, they must leave their home and explore the regions of Pandora. When an ancient threat resurfaces, Jake must fight a difficult war against the humans.",
        "James Cameron",
        "Sam Worthington, Zoe Saldaña",
        "https://m.media-amazon.com/images/M/MV5BNWI0Y2NkOWEtMmM2OC00MjQ3LWI1YzItZGQxYzQ3NzI4NWZmXkEyXkFqcGc@._V1_FMjpg_UX900_.jpg"
    ),
    (
        "Avatar",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "2009",
        "M",
        "Jake Sully, a paraplegic former Marine, becomes part of a corporate mission on the alien world of Pandora, where he bonds with the indigenous Na'vi and must choose between following orders or protecting his new home.",
        "James Cameron",
        "Sam Worthington, Zoe Saldaña, Sigourney Weaver",
        "https://m.media-amazon.com/images/M/MV5BMDEzMmQwZjctZWU2My00MWNlLWE0NjItMDJlYTRlNGJiZjcyXkEyXkFqcGc@._V1_FMjpg_UY2902_.jpg"
    ),
    (
        "Your Name.",
        "Romance", "Drama", "Fantasy", "Supernatural",
        "2016",
        "PG",
        "Two teenagers mysteriously begin swapping bodies, forming a deep connection that transcends distance and time as they try to meet in the real world.",
        "Makoto Shinkai",
        "Ryunosuke Kamiki, Mone Kamishiraishi",
        "https://m.media-amazon.com/images/M/MV5BMjI1ODZkYTgtYTY3Yy00ZTJkLWFkOTgtZDUyYWM4MzQwNjk0XkEyXkFqcGc@._V1_FMjpg_UY12000_.jpg"
    ),
    (
        "The Avengers",
        "Action", "Sci-Fi", "Adventure", "Superhero",
        "2012",
        "M",
        "Nick Fury of S.H.I.E.L.D. assembles a team of powerful heroes to stop Loki and his alien army from conquering Earth.",
        "Joss Whedon",
        "Robert Downey Jr., Chris Evans, Scarlett Johansson",
        "https://m.media-amazon.com/images/M/MV5BNGE0YTVjNzUtNzJjOS00NGNlLTgxMzctZTY4YTE1Y2Y1ZTU4XkEyXkFqcGc@._V1_FMjpg_UX800_.jpg"
    ),
    (
        "Avengers: Age of Ultron",
        "Action", "Sci-Fi", "Adventure", "Superhero",
        "2015",
        "M",
        "Tony Stark and Bruce Banner create an artificial intelligence called Ultron to protect humanity, but the sentient being turns against its creators, forcing the Avengers to stop a global extinction event.",
        "Joss Whedon",
        "Robert Downey Jr., Chris Evans, Scarlett Johansson",
        "https://m.media-amazon.com/images/M/MV5BODBhYTg1NGQtNGVmNS00ZTdiLThjYTYtZDFkNzRiNTZmNDZjXkEyXkFqcGc@._V1_FMjpg_UX864_.jpg"
    ),
    (
        "Avengers: Infinity War",
        "Action", "Sci-Fi", "Adventure", "Superhero",
        "2018",
        "M",
        "The Avengers and their allies unite to stop Thanos from collecting the Infinity Stones and carrying out his catastrophic plan to reshape the universe.",
        "Anthony Russo, Joe Russo",
        "Robert Downey Jr., Chris Evans, Josh Brolin",
        "https://m.media-amazon.com/images/M/MV5BMjMxNjY2MDU1OV5BMl5BanBnXkFtZTgwNzY1MTUwNTM@._V1_FMjpg_UY2048_.jpg"
    ),
    (
        "Avengers: Endgame",
        "Action", "Sci-Fi", "Adventure", "Superhero",
        "2019",
        "M",
        "After Thanos annihilates half of all life, the remaining Avengers assemble one final time to reverse his actions and restore balance to the universe.",
        "Anthony Russo, Joe Russo",
        "Robert Downey Jr., Chris Evans, Mark Ruffalo",
        "https://m.media-amazon.com/images/M/MV5BMTc5MDE2ODcwNV5BMl5BanBnXkFtZTgwMzI2NzQ2NzM@._V1_FMjpg_UY2048_.jpg"
    ),
    (
        "PK",
        "Comedy", "Drama", "Sci-Fi", "Satire",
        "2014",
        "M",
        "An innocent alien stranded on Earth embarks on a quest to retrieve his lost communication device, questioning religious dogma and social norms along the way.",
        "Rajkumar Hirani",
        "Aamir Khan, Anushka Sharma",
        "https://m.media-amazon.com/images/M/MV5BMTYzOTE2NjkxN15BMl5BanBnXkFtZTgwMDgzMTg0MzE@._V1_FMjpg_UX1090_.jpg"
    ),
    (
        "RRR",
        "Action", "Drama", "Historical", "Epic",
        "2022",
        "MA 15+",
        "Two legendary revolutionaries with opposing paths form an unbreakable bond and rise together to fight against British colonial rule in India.",
        "S. S. Rajamouli",
        "N. T. Rama Rao Jr., Ram Charan",
        "https://m.media-amazon.com/images/M/MV5BNWMwODYyMjQtMTczMi00NTQ1LWFkYjItMGJhMWRkY2E3NDAyXkEyXkFqcGc@._V1_FMjpg_UX750_.jpg"
    ),
    (
        "K.G.F: Chapter 1",
        "Action", "Drama", "Crime", "Thriller",
        "2018",
        "MA 15+",
        "Rocky, a young man, seeks power and wealth in order to fulfil a promise to his dying mother. His quest takes him to Mumbai, where he becomes entangled with the notorious gold mafia.",
        "Prashanth Neel",
        "Yash, Srinidhi Shetty",
        "https://m.media-amazon.com/images/M/MV5BM2M0YmIxNzItOWI4My00MmQzLWE0NGYtZTM3NjllNjIwZjc5XkEyXkFqcGc@._V1_FMjpg_UX500_.jpg"
    ),
    (
        "K.G.F: Chapter 2",
        "Action", "Drama", "Crime", "Thriller",
        "2022",
        "MA 15+",
        "Rocky rises as the leader and saviour of the Kolar Gold Fields, facing new enemies like Adheera, Inayat Khalil, and Ramika Sen while trying to fulfil his mother’s last wishes.",
        "Prashanth Neel",
        "Yash, Sanjay Dutt, Raveena Tandon",
        "https://m.media-amazon.com/images/M/MV5BZmQzZjVkZTUtYjI4ZC00ZDJmLWI0ZDUtZTFmMGM1Mzc5ZjIyXkEyXkFqcGc@._V1_FMjpg_UY2408_.jpg"
    ),
    (
        "Baahubali: The Beginning",
        "Action", "Adventure", "Fantasy", "Drama",
        "2015",
        "MA 15+",
        "In the kingdom of Mahishmati, Shivudu falls in love with a warrior woman and uncovers the conflict-ridden past of his family and his true legacy.",
        "S.S. Rajamouli",
        "Prabhas, Tamannaah, Rana Daggubati",
        "https://m.media-amazon.com/images/M/MV5BNmNlYWMyYWUtMmVlNy00MzFkLTgxYTQtYzQ5ZTU1ZGYyNjYyXkEyXkFqcGc@._V1_FMjpg_UX620_.jpg"
    ),
    (
        "Baahubali 2: The Conclusion",
        "Action", "Adventure", "Fantasy", "Drama",
        "2017",
        "MA 15+",
        "After discovering that his father was killed by Bhallaladeva, Mahendra Baahubali raises an army to defeat him and free his mother from captivity.",
        "S.S. Rajamouli",
        "Prabhas, Anushka Shetty, Rana Daggubati",
        "https://m.media-amazon.com/images/M/MV5BNTRhYTlhZTgtYmMyYy00NWI4LTk4MzItOWM2YjBmYTg2OTI2XkEyXkFqcGc@._V1_FMjpg_UX1129_.jpg"
    ),
    (
        "Baahubali: The Epic",
        "Action", "Adventure", "Fantasy", "Drama",
        "2017",
        "MA 15+",
        "Mahendra returns to the ancient kingdom of Mahishmati to avenge his father's death and reclaim his rightful place.",
        "S.S. Rajamouli",
        "Prabhas, Anushka Shetty, Rana Daggubati",
        "https://m.media-amazon.com/images/M/MV5BNmIwYTI3ODItMzRkOS00MzlhLWI4NzQtNDFmOGJhZGJhM2VkXkEyXkFqcGc@._V1_FMjpg_UX1080_.jpg"
    ),
    (
        "Golmaal Again",
        "Comedy", "Horror", "Family", "Drama",
        "2017",
        "M",
        "Five orphan men return to the orphanage they grew up in to attend their mentor's funeral. They encounter the ghost of their childhood friend, Khushi, and help her attain salvation.",
        "Rohit Shetty",
        "Ajay Devgn, Parineeti Chopra, Tabu",
        "https://m.media-amazon.com/images/M/MV5BZDljYzk0MzgtY2ZlMi00MjQ1LTk0MzYtZGFiZjdiM2VkMWU3XkEyXkFqcGc@._V1_FMjpg_UY2250_.jpg"
    ),
    (
        "Johnny English",
        "Comedy", "Action", "Spy", "Adventure",
        "2003",
        "PG",
        "After all MI5 agents are killed, the intellectually challenged yet confident spy Johnny English takes charge of all operations.",
        "Peter Howitt",
        "Rowan Atkinson, Natalie Imbruglia",
        "https://m.media-amazon.com/images/M/MV5BMTU0MGM4ZjQtNmQ3MC00NDE4LWEwYTItYWZiYzAxMGQwMDkzXkEyXkFqcGc@._V1_FMjpg_UX800_.jpg"
    ),
    (
        "Johnny English Reborn",
        "Comedy", "Action", "Spy", "Adventure",
        "2011",
        "PG",
        "Eight years after a failed mission, Johnny English returns to MI-7 to stop international assassins from killing the Chinese premier.",
        "Oliver Parker",
        "Rowan Atkinson, Rosamund Pike",
        "https://m.media-amazon.com/images/M/MV5BYjNhMTRlYWMtNGQzZS00OGFmLTlhOGUtODZlMDY4YzNlZDYwXkEyXkFqcGc@._V1_FMjpg_UX1013_.jpg"
    ),
    (
        "Johnny English Strikes Again",
        "Comedy", "Action", "Spy", "Adventure",
        "2018",
        "PG",
        "When a hacker exposes undercover agents in Britain, Johnny English is hired to find the culprit.",
        "David Kerr",
        "Rowan Atkinson, Ben Miller",
        "https://m.media-amazon.com/images/M/MV5BOTkzNTEzOTk5MV5BMl5BanBnXkFtZTgwNDk1OTYzNjM@._V1_FMjpg_UX510_.jpg"
    ),
    (
        "Inception",
        "Sci-Fi", "Action", "Thriller", "Mystery",
        "2010",
        "M",
        "Cobb steals information from targets by entering their dreams. Wanted for his wife's murder, his only chance at redemption is performing an impossible task.",
        "Christopher Nolan",
        "Leonardo DiCaprio, Joseph Gordon-Levitt, Ellen Page",
        "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_FMjpg_UX700_.jpg"
    ),
    (
        "The Matrix",
        "Sci-Fi", "Action", "Adventure", "Thriller",
        "1999",
        "M",
        "Neo, a hacker, discovers the reality he lives in is a simulated world, and joins Morpheus to learn the truth.",
        "Lana Wachowski, Lilly Wachowski",
        "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
        "https://m.media-amazon.com/images/M/MV5BN2NmN2VhMTQtMDNiOS00NDlhLTliMjgtODE2ZTY0ODQyNDRhXkEyXkFqcGc@._V1_FMjpg_UY3156_.jpg"
    ),
    (
        "Matrix Reloaded",
        "Action", "Sci-Fi", "Adventure", "Thriller",
        "2003",
        "M",
        "Neo attempts to rescue the Keymaker from the Merovingian. He must confront the Architect to save Zion, while Zion prepares for war against the machines.",
        "Lana Wachowski, Lilly Wachowski",
        "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
        "https://m.media-amazon.com/images/M/MV5BNjAxYjkxNjktYTU0YS00NjFhLWIyMDEtMzEzMTJjMzRkMzQ1XkEyXkFqcGc@._V1_FMjpg_UX800_.jpg"
    ),
    (
        "Matrix Revolutions",
        "Action", "Sci-Fi", "Adventure", "Thriller",
        "2003",
        "M",
        "Neo attempts to broker peace between humans and machines to save Zion, confronting his arch-nemesis, the rogue agent Smith.",
        "Lana Wachowski, Lilly Wachowski",
        "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
        "https://m.media-amazon.com/images/M/MV5BMmNmMTEzODQtNmExMS00OGUxLWFkNTItMTM3NzBlNDk0YWU5XkEyXkFqcGc@._V1_FMjpg_UY3251_.jpg"
    ),
    (
        "The Matrix Resurrections",
        "Action", "Sci-Fi", "Adventure", "Thriller",
        "2021",
        "M",
        "Thomas Anderson accepts Morpheus's offer and discovers a new, more secure, and dangerous Matrix.",
        "Lana Wachowski",
        "Keanu Reeves, Carrie-Anne Moss, Yahya Abdul-Mateen II",
        "https://m.media-amazon.com/images/M/MV5BMDMyNDIzYzMtZTMyMy00NjUyLWI3Y2MtYzYzOGE1NzQ1MTBiXkEyXkFqcGc@._V1_FMjpg_UY4096_.jpg"
    ),
    (
        "Pirates of the Caribbean: The Curse of the Black Pearl",
        "Action", "Adventure", "Fantasy", "Comedy",
        "2003",
        "M",
        "Will joins Captain Jack Sparrow to rescue Elizabeth, kidnapped due to her supposed possession of Jack's medallion.",
        "Gore Verbinski",
        "Johnny Depp, Orlando Bloom, Keira Knightley",
        "https://m.media-amazon.com/images/M/MV5BNDhlMzEyNzItMTA5Mi00YWRhLThlNTktYTQyMTA0MDIyNDEyXkEyXkFqcGc@._V1_FMjpg_UX671_.jpg"
    ),
    (
        "Pirates of the Caribbean: Dead Man's Chest",
        "Action", "Adventure", "Fantasy", "Comedy",
        "2006",
        "M",
        "Jack Sparrow seeks the heart of Davy Jones to avoid enslavement. Will and Elizabeth also have their own motives.",
        "Gore Verbinski",
        "Johnny Depp, Orlando Bloom, Keira Knightley",
        "https://m.media-amazon.com/images/M/MV5BMTcwODc1MTMxM15BMl5BanBnXkFtZTYwMDg1NzY3._V1_FMjpg_UX450_.jpg"
    ),
    (
        "Pirates of the Caribbean: At World's End",
        "Action", "Adventure", "Fantasy", "Comedy",
        "2007",
        "M",
        "Will Turner and Elizabeth Swann team up with Barbossa to rescue Jack Sparrow and confront the Flying Dutchman.",
        "Gore Verbinski",
        "Johnny Depp, Orlando Bloom, Keira Knightley",
        "https://m.media-amazon.com/images/M/MV5BMjIyNjkxNzEyMl5BMl5BanBnXkFtZTYwMjc3MDE3._V1_FMjpg_UX450_.jpg"
    ),
    (
        "Pirates of the Caribbean: On Stranger Tides",
        "Action", "Adventure", "Fantasy", "Comedy",
        "2011",
        "M",
        "Jack Sparrow searches for the Fountain of Youth, encountering a mysterious woman and facing his old enemy Blackbeard.",
        "Rob Marshall",
        "Johnny Depp, Penélope Cruz, Ian McShane",
        "https://m.media-amazon.com/images/M/MV5BMjE5MjkwODI3Nl5BMl5BanBnXkFtZTcwNjcwMDk4NA@@._V1_FMjpg_UX1114_.jpg"
    ),
    (
        "Pirates of the Caribbean: Dead Men Tell No Tales",
        "Action", "Adventure", "Fantasy", "Comedy",
        "2017",
        "M",
        "Jack Sparrow and Henry Turner search for the Trident of Poseidon to break the Flying Dutchman's curse and stop Captain Salazar.",
        "Joachim Rønning, Espen Sandberg",
        "Johnny Depp, Brenton Thwaites, Kaya Scodelario",
        "https://m.media-amazon.com/images/M/MV5BMTYyMTcxNzc5M15BMl5BanBnXkFtZTgwOTg2ODE2MTI@._V1_FMjpg_UY2048_.jpg"
    ),
    (
        "Star Wars: Episode IV - A New Hope",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "1977",
        "PG",
        "Princess Leia is abducted by Darth Vader. Luke teams up with a Jedi, a pilot, and two droids to save her and the galaxy.",
        "George Lucas",
        "Mark Hamill, Carrie Fisher, Harrison Ford",
        "https://m.media-amazon.com/images/M/MV5BOGUwMDk0Y2MtNjBlNi00NmRiLTk2MWYtMGMyMDlhYmI4ZDBjXkEyXkFqcGc@._V1_FMjpg_UY2937_.jpg"
    ),
    (
        "Star Wars: Episode V - The Empire Strikes Back",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "1980",
        "PG",
        "The Rebel Alliance fights the Galactic Empire while Luke Skywalker attempts to master the Force and become a Jedi.",
        "Irvin Kershner",
        "Mark Hamill, Carrie Fisher, Harrison Ford",
        "https://m.media-amazon.com/images/M/MV5BMTkxNGFlNDktZmJkNC00MDdhLTg0MTEtZjZiYWI3MGE5NWIwXkEyXkFqcGc@._V1_FMjpg_UY2883_.jpg"
    ),
    (
        "Star Wars: Episode VI - Return of the Jedi",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "1983",
        "PG",
        "Luke Skywalker tries to bring his father to the light side while the rebels hatch a plan to destroy the second Death Star.",
        "Richard Marquand",
        "Mark Hamill, Carrie Fisher, Harrison Ford",
        "https://m.media-amazon.com/images/M/MV5BNWEwOTI0MmUtMGNmNy00ODViLTlkZDQtZTg1YmQ3MDgyNTUzXkEyXkFqcGc@._V1_FMjpg_UY2809_.jpg"
    ),
    (
        "Star Wars: Episode I - The Phantom Menace",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "1999",
        "PG",
        "Jedi Qui-Gon and Obi-Wan protect a princess and discover a boy strong in the Force.",
        "George Lucas",
        "Liam Neeson, Ewan McGregor, Natalie Portman",
        "https://m.media-amazon.com/images/M/MV5BODVhNGIxOGItYWNlMi00YTA0LWI3NTctZmQxZGUwZDEyZWI4XkEyXkFqcGc@._V1_FMjpg_UX1230_.jpg"
    ),
    (
        "Star Wars: Episode II - Attack of the Clones",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "2002",
        "PG",
        "Obi-Wan uncovers a plot to destroy the Republic, and the Jedi must defend the galaxy against the Sith.",
        "George Lucas",
        "Ewan McGregor, Natalie Portman, Hayden Christensen",
        "https://m.media-amazon.com/images/M/MV5BNTgxMjY2YzUtZmVmNC00YjAwLWJlODMtNDBhNzllNzIzMjgxXkEyXkFqcGc@._V1_FMjpg_UY3091_.jpg"
    ),
    (
        "Star Wars: Episode III - Revenge of the Sith",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "2005",
        "M",
        "Anakin falls prey to Palpatine and the Jedi's mind games, giving into temptation.",
        "George Lucas",
        "Ewan McGregor, Natalie Portman, Hayden Christensen",
        "https://m.media-amazon.com/images/M/MV5BNTc4MTc3NTQ5OF5BMl5BanBnXkFtZTcwOTg0NjI4NA@@._V1_FMjpg_UX1152_.jpg"
    ),
    (
        "Star Wars: The Force Awakens",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "2015",
        "M",
        "Finn, Rey, and Poe must stop a new order from destroying the New Republic and find the last surviving Jedi, Luke.",
        "J.J. Abrams",
        "Daisy Ridley, John Boyega, Harrison Ford",
        "https://m.media-amazon.com/images/M/MV5BOTAzODEzNDAzMl5BMl5BanBnXkFtZTgwMDU1MTgzNzE@._V1_FMjpg_UY3240_.jpg"
    ),
    (
        "Star Wars: The Last Jedi",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "2017",
        "M",
        "Luke trains Rey to assist the Resistance against the First Order while she develops her powers.",
        "Rian Johnson",
        "Daisy Ridley, John Boyega, Mark Hamill",
        "https://m.media-amazon.com/images/M/MV5BMjQ1MzcxNjg4N15BMl5BanBnXkFtZTgwNzgwMjY4MzI@._V1_FMjpg_UX800_.jpg"
    ),
    (
        "Star Wars: The Rise of Skywalker",
        "Sci-Fi", "Adventure", "Action", "Fantasy",
        "2019",
        "M",
        "Emperor Palpatine is resurrected, and the Jedi face off against the Sith in the final battle of the saga.",
        "J.J. Abrams",
        "Daisy Ridley, John Boyega, Adam Driver",
        "https://m.media-amazon.com/images/M/MV5BODg5ZTNmMTUtYThlNy00NjljLWE0MGUtYmQ1NDg4NWU5MjQ1XkEyXkFqcGc@._V1_FMjpg_UY2048_.jpg"
    ),
        (
        "One Piece Film: Red",
        "Adventure", "Fantasy", "Action", "Music",
        "2022",
        "PG",
        "Uta is a beloved singer, renowned for concealing her identity. For the first time ever, she reveals herself at a live concert.",
        "Gorō Taniguchi",
        "Kaori Nazuka, Kazuya Nakai, Shunya Shiraishi",
        "https://m.media-amazon.com/images/M/MV5BNTdjY2YxYTQtNjIzYy00ZDczLThhNTUtNmY2ZWNkZjZiMTYzXkEyXkFqcGc@._V1_FMjpg_UY5603_.jpg"
    ),
    (
        "Chainsaw Man - The Movie: Reze Arc",
        "Action", "Horror", "Supernatural", "Thriller",
        "2025",
        "MA 15+",
        "Chainsaw Man faces his deadliest battle yet in a brutal war between devils, hunters, and secret enemies.",
        "Ryu Nakayama",
        "Kikunosuke Toya, Reina Ueda, Tomori Kusunoki",
        "https://m.media-amazon.com/images/M/MV5BNDQzMjc2ZDQtMjY2NS00M2UxLTg2OTktNWVjZmY5YjA4MzVhXkEyXkFqcGc@._V1_FMjpg_UX1079_.jpg"
    ),
    (
        "Howl's Moving Castle",
        "Fantasy", "Adventure", "Romance", "Family",
        "2004",
        "PG",
        "Jealous of Sophie's closeness to Howl, the Witch of Waste transforms her into an old lady. Sophie must break the spell with Howl's friends, Calcifer and Markl.",
        "Hayao Miyazaki",
        "Chieko Baishō, Takuya Kimura, Akihiro Miwa",
        "https://m.media-amazon.com/images/M/MV5BNzlhNzlmZjktMTkyNC00ODBkLTlkZjctODAyMGRiYzQyMThmXkEyXkFqcGc@._V1_FMjpg_UX667_.jpg"
    ),
    (
        "The Lord of the Rings: The Fellowship of the Ring",
        "Fantasy", "Adventure", "Action", "Drama",
        "2001",
        "M",
        "A ring with mysterious powers lands with Frodo. Guided by Gandalf, he and his friends embark on a journey to the Elvish kingdom.",
        "Peter Jackson",
        "Elijah Wood, Ian McKellen, Orlando Bloom",
        "https://m.media-amazon.com/images/M/MV5BNzIxMDQ2YTctNDY4MC00ZTRhLTk4ODQtMTVlOWY4NTdiYmMwXkEyXkFqcGc@._V1_FMjpg_UY2936_.jpg"
    ),
    (
        "The Lord of the Rings: The Two Towers",
        "Fantasy", "Adventure", "Action", "Drama",
        "2002",
        "M",
        "Frodo and Sam arrive in Mordor with Gollum's help. Allies join to defend Isengard as Saruman launches his assault.",
        "Peter Jackson",
        "Elijah Wood, Ian McKellen, Viggo Mortensen",
        "https://m.media-amazon.com/images/M/MV5BMGQxMDdiOWUtYjc1Ni00YzM1LWE2NjMtZTg3Y2JkMjEzMTJjXkEyXkFqcGc@._V1_FMjpg_UX964_.jpg"
    ),
    (
        "The Lord of the Rings: The Return of the King",
        "Fantasy", "Adventure", "Action", "Drama",
        "2003",
        "M",
        "The Fellowship prepares for the final battle. Frodo and Sam approach Mount Doom to destroy the One Ring, following Gollum unknowingly.",
        "Peter Jackson",
        "Elijah Wood, Ian McKellen, Viggo Mortensen",
        "https://m.media-amazon.com/images/M/MV5BMTZkMjBjNWMtZGI5OC00MGU0LTk4ZTItODg2NWM3NTVmNWQ4XkEyXkFqcGc@._V1_FMjpg_UX800_.jpg"
    ),
    (
        "A Minecraft Movie",
        "Adventure", "Fantasy", "Family", "Comedy",
        "2025",
        "PG",
        "A mysterious portal pulls four misfits into the Overworld. To get back home, they'll master the terrain with the help of Steve.",
        "Aaron Horvath & Peter Rida Michail",
        "Jason Momoa, Jack Black, Emma Myers",
        "https://m.media-amazon.com/images/M/MV5BMjA0MWY0NTktMjJlNi00ZjhkLWI2ZTMtZDc0MjgxMjRkNzdkXkEyXkFqcGc@._V1_FMjpg_UY712_.jpg"
    ),
        (
        "Rush Hour", "Action", "Comedy", "Crime", "Adventure",
        "1998", "M",
        "Two cops from different cultures, who cannot stand each other, team up to save the kidnapped 11-year-old daughter of a diplomat.",
        "Brett Ratner",
        "Jackie Chan, Chris Tucker", 
        "https://m.media-amazon.com/images/M/MV5BMGZiMzViNmEtNTNlZi00MzFmLTk5NTEtNDE2OTUzNmNlMTY4XkEyXkFqcGc@._V1_FMjpg_UX850_.jpg"
    ),
    (
        "Rush Hour 2", "Action", "Comedy", "Crime", "Adventure",
        "2001", "M",
        "While vacationing in Hong Kong, Lee is assigned to solve a case after a bomb kills two undercover agents.",
        "Brett Ratner",
        "Jackie Chan, Chris Tucker", 
        "https://m.media-amazon.com/images/M/MV5BMGM0OTM4NGYtYzkzMC00OGZmLWEwZTItOTg4ZTdkYTIxOTc0XkEyXkFqcGc@._V1_FMjpg_UX1011_.jpg"
    ),
    (
        "Rush Hour 3", "Action", "Comedy", "Crime", "Adventure",
        "2007", "M",
        "Inspector Lee and Detective Carter arrive in Paris following a murder attempt on Ambassador Han and track down the Triads' secret leaders.",
        "Brett Ratner",
        "Jackie Chan, Chris Tucker", 
        "https://m.media-amazon.com/images/M/MV5BMTA0Nzg5NjQ0MDBeQTJeQWpwZ15BbWU3MDE4Mzg5NDE@._V1_FMjpg_UX510_.jpg"
    ),
    (
        "Ip Man", "Action", "Biography", "Drama", "History",
        "2008", "MA 15+",
        "After the Japanese invasion, Ip Man refuses to train enemy soldiers despite his skills becoming known.",
        "Wilson Yip",
        "Donnie Yen", 
        "https://m.media-amazon.com/images/M/MV5BZmJjZDE0MmYtNzgwYy00NTg2LWE0NDYtNzA0YTA4MjA0NmYxXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
    ),
    (
        "Kung Fu Panda", "Animation", "Action", "Comedy", "Family",
        "2008", "G",
        "Po, a kung fu enthusiast, is selected as the Dragon Warrior and must team up with the Furious Five to defeat evil forces.",
        "Mark Osborne & John Stevenson",
        "Jack Black, Dustin Hoffman", 
        "https://m.media-amazon.com/images/M/MV5BZDU5MDNiMGItYjVmZi00NDUxLTg2OTktNGE0NzNlNzM4NzgyXkEyXkFqcGc@._V1_FMjpg_UY2048_.jpg"
    ),
    (
        "Kung Fu Panda 2", "Animation", "Action", "Comedy", "Family",
        "2011", "G",
        "Dragon Warrior Po uncovers the mystery of his past while stopping the evil peacock Shen from conquering China.",
        "Jennifer Yuh Nelson",
        "Jack Black, Angelina Jolie", 
        "https://m.media-amazon.com/images/M/MV5BYmIxMGYzMTUtZDQzYy00ODc4LWE1YzQtZGMwYTc0YTYyYTE0XkEyXkFqcGc@._V1_FMjpg_UX482_.jpg"
    ),
    (
        "Kung Fu Panda 3", "Animation", "Action", "Comedy", "Family",
        "2016", "G",
        "Po must train a group of pandas to master kung fu to defeat the wicked supernatural warrior Kai.",
        "Jennifer Yuh Nelson & Alessandro Carloni",
        "Jack Black, Bryan Cranston", 
        "https://m.media-amazon.com/images/M/MV5BMTUyNzgxNjg2M15BMl5BanBnXkFtZTgwMTY1NDI1NjE@._V1_FMjpg_UX660_.jpg"
    ),
    (
        "Ice Age", "Animation", "Adventure", "Comedy", "Family",
        "2002", "G",
        "Manny, Sid, and Diego help return a human baby to his father during the onset of an ice age.",
        "Chris Wedge",
        "Ray Romano, John Leguizamo", 
        "https://m.media-amazon.com/images/M/MV5BMDBlYzU2OGMtOGJjNi00ZGZjLWIwNjMtYzdiZjkwYWNjZDljXkEyXkFqcGc@._V1_FMjpg_UX691_.jpg"
    ),
    (
        "Ice Age: The Meltdown", "Animation", "Adventure", "Comedy", "Family",
        "2006", "G",
        "Manny, Sid, and Diego search for higher ground as water bursts from a glacier, caused by Scrat's acorn mishap.",
        "Carlos Saldanha",
        "Ray Romano, John Leguizamo", 
        "https://m.media-amazon.com/images/M/MV5BMjAwODg3OTAxMl5BMl5BanBnXkFtZTcwMjg2NjYyMw@@._V1_FMjpg_UY2048_.jpg"
    ),
    (
        "Ice Age: Dawn of the Dinosaurs", "Animation", "Adventure", "Comedy", "Family",
        "2009", "G",
        "Manny and Ellie expect their first child while Sid steals dinosaur eggs, leading to a rescue mission.",
        "Carlos Saldanha",
        "Ray Romano, John Leguizamo", 
        "https://m.media-amazon.com/images/M/MV5BZWJjZDYwMjgtZDZiMy00YzcyLThjN2YtYjI1ZDQ2ZDJkOTVmXkEyXkFqcGc@._V1_FMjpg_UY2110_.jpg"
    ),
    (
        "Ice Age: Continental Drift", "Animation", "Adventure", "Comedy", "Family",
        "2012", "G",
        "Scrat's nut-chasing antics cause a continental drift, dragging Manny, Diego, and Sid into another adventure.",
        "Steve Martino & Mike Thurmeier",
        "Ray Romano, John Leguizamo", 
        "https://m.media-amazon.com/images/M/MV5BMTM3NDM5MzY5Ml5BMl5BanBnXkFtZTcwNjExMDUwOA@@._V1_FMjpg_UY2000_.jpg"
    ),
    (
        "Madagascar", "Animation", "Comedy", "Adventure", "Family",
        "2005", "G",
        "Four animals from New York Central Zoo escape to Madagascar, where they meet happy lemurs.",
        "Eric Darnell & Tom McGrath",
        "Ben Stiller, Chris Rock", 
        "https://m.media-amazon.com/images/M/MV5BYjk4OGFmZmYtYWE4NC00MzM4LTkwZTItODdhMjk3NTZjMmI5XkEyXkFqcGc@._V1_FMjpg_UX960_.jpg"
    ),
    (
        "Madagascar: Escape 2 Africa", "Animation", "Comedy", "Adventure", "Family",
        "2008", "G",
        "Alex reunites with his long-lost parents in Africa while Makunga tries to become king of the jungle.",
        "Eric Darnell & Tom McGrath",
        "Ben Stiller, Chris Rock", 
        "https://m.media-amazon.com/images/M/MV5BMjExMDA4NDcwMl5BMl5BanBnXkFtZTcwODAxNTQ3MQ@@._V1_FMjpg_UX550_.jpg"
    ),
    (
        "Madagascar 3: Europe's Most Wanted", "Animation", "Comedy", "Adventure", "Family",
        "2012", "G",
        "The zoo animals travel across Europe with a circus troupe while being chased by animal control.",
        "Eric Darnell & Tom McGrath",
        "Ben Stiller, Chris Rock", 
        "https://m.media-amazon.com/images/M/MV5BYTM5OWRiZTAtOTNkMS00NzNhLTkwYmYtMWI1MzkyMjE3MWE1XkEyXkFqcGc@._V1_FMjpg_UX800_.jpg"
    ),
    (
        "Guardians of the Galaxy", "Action", "Adventure", "Comedy", "Sci-Fi",
        "2014", "M",
        "A group of skilled criminals led by Peter Quill join forces to stop villain Ronan the Accuser, who wants a mystical orb to control the universe.",
        "James Gunn",
        "Chris Pratt, Zoe Saldana, Dave Bautista",
        "https://m.media-amazon.com/images/M/MV5BM2ZmNjQ2MzAtNDlhNi00MmQyLWJhZDMtNmJiMjFlOWY4MzcxXkEyXkFqcGc@._V1_FMjpg_UX1012_.jpg"
    ),
    (
        "Guardians of the Galaxy Vol. 2", "Action", "Adventure", "Comedy", "Sci-Fi",
        "2017", "M",
        "After a successful mission, Peter Quill and his team meet Ego, who claims to be Peter's father, but uncover disturbing truths.",
        "James Gunn",
        "Chris Pratt, Zoe Saldana, Dave Bautista",
        "https://m.media-amazon.com/images/M/MV5BNWE5MGI3MDctMmU5Ni00YzI2LWEzMTQtZGIyZDA5MzQzNDBhXkEyXkFqcGc@._V1_FMjpg_UX509_.jpg"
    ),
    (
        "Guardians of the Galaxy Vol. 3", "Action", "Adventure", "Comedy", "Sci-Fi",
        "2023", "M",
        "Peter Quill and his team must rally to defend the universe and protect one of their own, or risk the end of the Guardians.",
        "James Gunn",
        "Chris Pratt, Zoe Saldana, Dave Bautista",
        "https://m.media-amazon.com/images/M/MV5BOTJhOTMxMmItZmE0Ny00MDc3LWEzOGEtOGFkMzY4MWYyZDQ0XkEyXkFqcGc@._V1_FMjpg_UX886_.jpg"
    ),
    (
        "Doctor Strange", "Action", "Adventure", "Fantasy", "Sci-Fi",
        "2016", "M",
        "After losing the use of his hands, Stephen Strange trains under the Ancient One and becomes a master sorcerer.",
        "Scott Derrickson",
        "Benedict Cumberbatch, Chiwetel Ejiofor",
        "https://m.media-amazon.com/images/M/MV5BNjgwNzAzNjk1Nl5BMl5BanBnXkFtZTgwMzQ2NjI1OTE@._V1_FMjpg_UY2048_.jpg"
    ),
    (
        "Doctor Strange in the Multiverse of Madness", "Action", "Adventure", "Fantasy", "Sci-Fi",
        "2022", "M",
        "Doctor Strange teams with a mysterious teenage girl to battle multiverse threats, including alternate versions of himself.",
        "Sam Raimi",
        "Benedict Cumberbatch, Elizabeth Olsen",
        "https://m.media-amazon.com/images/M/MV5BMGMwYmVlYTEtYmZhMC00ZDQ3LTgwNWMtZjBkNjEzZDkxOWFlXkEyXkFqcGc@._V1_FMjpg_UX756_.jpg"
    ),
    (
        "Jurassic Park", "Adventure", "Sci-Fi", "Action", "Adventure", 
        "1993", "PG", 
        "An industrialist invites some experts to visit his theme park of cloned dinosaurs. After a power failure, the creatures run loose, putting everyone's lives, including his grandchildren's, in danger.", 
        "Steven Spielberg", 
        "Sam Neill, Laura Dern, Jeff Goldblum", 
        "https://m.media-amazon.com/images/M/MV5BMjM2MDgxMDg0Nl5BMl5BanBnXkFtZTgwNTM2OTM5NDE@._V1_FMjpg_UX667_.jpg"
    ),
    (
        "Whiplash", "Drama", "Music", "Psychological", "Drama", 
        "2014", "M", 
        "Andrew enrols in a music conservatory to become a drummer. But he is mentored by Terence Fletcher, whose unconventional training methods push him beyond the boundaries of reason and sensibility.", 
        "Damien Chazelle", 
        "Miles Teller, J.K. Simmons", 
        "https://m.media-amazon.com/images/M/MV5BMDFjOWFkYzktYzhhMC00NmYyLTkwY2EtYjViMDhmNzg0OGFkXkEyXkFqcGc@._V1_FMjpg_UY5333_.jpg"
    ),
    (
        "KPop Demon Hunters", "Action", "Fantasy", "Music", "Adventure", 
        "2025", "M", 
        "When K-pop superstars Rumi, Mira and Zoey aren't selling out stadiums or topping the Billboard charts, they're moonlighting as demon hunters to protect their fans from ever-present supernatural danger.", 
        "Saja Boys", 
        "Rumi, Mira, Zoey", 
        "https://m.media-amazon.com/images/M/MV5BNTBiYWJlMjQtOTIyMy00NTY4LWFhOWItOWZhNzc3NGMyMjc2XkEyXkFqcGc@._V1_FMjpg_UX1013_.jpg"
    ),
    (
        "Interstellar", "Sci-Fi", "Adventure", "Drama", "Sci-Fi", 
        "2014", "M", 
        "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft, along with a team of researchers, to find a new planet for humans.", 
        "Christopher Nolan", 
        "Matthew McConaughey, Anne Hathaway, Jessica Chastain", 
        "https://m.media-amazon.com/images/M/MV5BYzdjMDAxZGItMjI2My00ODA1LTlkNzItOWFjMDU5ZDJlYWY3XkEyXkFqcGc@._V1_FMjpg_UY3600_.jpg"
    ),
    (
        "The Dark Knight", "Action", "Crime", "Drama", "Thriller", 
        "2008", "M", 
        "Batman has a new foe, the Joker, who is an accomplished criminal hell-bent on decimating Gotham City. Together with Gordon and Harvey Dent, Batman struggles to thwart the Joker before it is too late.", 
        "Christopher Nolan", 
        "Christian Bale, Heath Ledger, Aaron Eckhart", 
        "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_FMjpg_UY2048_.jpg"
    )
    ]

    cursor.executemany("""
    INSERT INTO MovieList (
        FilmName, FilmGenreP, FilmGenreS, FilmGenreT, FilmGenreQ,
        FilmReleaseDate, FilmClassification, FilmDescription,
        FilmDirectors, FilmActors, FlimImageLink
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, movies)


    conn.commit()


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
            elif choice == "4":
                list_all_movies()
            elif choice == "5":
                browse_movies_terminal()
            elif choice == "6":
                search_movies_terminal()
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
                elif choice == "7":
                    list_all_movies()
                elif choice == "8":
                    browse_movies_terminal()
                elif choice == "9":
                    search_movies_terminal()
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
                elif choice == "0":
                    list_all_movies()
                elif choice.upper() == "B":
                    browse_movies_terminal()
                elif choice.upper() == "S":
                    search_movies_terminal()
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
                elif choice.upper() == "X":
                    list_all_movies()
                elif choice.upper() == "B":
                    browse_movies_terminal()
                elif choice.upper() == "S":
                    search_movies_terminal()
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
                elif choice.upper() == "X":
                    list_all_movies()
                elif choice.upper() == "B":
                    browse_movies_terminal()
                elif choice.upper() == "S":
                    search_movies_terminal()
                else:
                    print("Not implemented yet or invalid option.")





conn.close()