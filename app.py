from flask import Flask, render_template, request, redirect, url_for, jsonify
import PyPDF2, openai
import sqlite3
import multiprocessing
import time
import googleapiclient.discovery

app = Flask(__name__)
app.secret_key = 'ENTER YOUR OWN KEY'

conn = sqlite3.connect('QPAdatabase.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT,
                    password TEXT
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS qpapers (
                    subject TEXT,
                    qname TEXT,
                    qtext TEXT
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS samplepapers (
                    subject TEXT,
                    partA TEXT,
                    partB TEXT
                )''')
conn.commit()
conn.close()


openai.api_key = "ENTER YOUR OWN KEY"
API_KEY = "ENTER YOUR OWN KEY"



bank = " "
file = " "
subject = " "
subname = " "
faq = " "

# function 1
def gpt3function(input):
    if input:
        messages = [
        {"role": "system", "content": ""},
        ]
        messages.append({"role": "user", "content": input})
        answer = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
        reply = answer.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        formatted_reply = ""
        bullet_counter = 1
        for line in reply.splitlines():
            if line.strip().startswith(str(bullet_counter) + "."):
                formatted_reply += line + "\n"
                bullet_counter += 1
            elif ":" in line:
                parts = line.split(":")
                formatted_reply += parts[0] + ":\n" + ":".join(parts[1:]) + "\n"
            else:
                formatted_reply += line + "\n"
        formatted_reply = formatted_reply + "\n"
        return formatted_reply



#function 2
def pdfreader(file):
    #global bank
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_number in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_number].extract_text()
    
    qname = file.filename
    qtext = text
    conn = sqlite3.connect('QPAdatabase.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO qpapers (subject, qname, qtext) SELECT ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM qpapers WHERE qname = ?)", (subject, qname, qtext, qname))
    conn.commit()
    conn.close()
    
    #bank=bank+text



#function 3
def insert_user(username, password):
    conn = sqlite3.connect('QPAdatabase.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

#function 4
def subjectname(sub):
    if sub == "NN":
        return "Neural Networks"
    elif sub == "DM":
        return "Data Mining"
    elif sub == "CC":
        return "Compiler Construction"
    elif sub == "CN":
        return "Computer Networks"
    elif sub == "OS":
        return "Operating Systems"
    elif sub == "ADA":
        return "Analysis and Design of Algorithms"
    elif sub == "LD":
        return "Logic Design"
    elif sub == "DCS":
        return "Discrete Computational Structures"
    elif sub == "OOP":
        return "Object Oriented Programming"
    elif sub == "PPL":
        return "Principles of Programming Languages"
    elif sub == "DCC":
        return "Data and Computer Communication"
    elif sub == "MP":
        return "Microprocessors"
    elif sub == "CAO":
        return "Computer Architecture and Organization"
    elif sub == "ALC":
        return "Automata Languages and Computations"
    elif sub == "DSA":
        return "Data Structures and Algorithms"
    elif sub == "DBMS":
        return "Database Management Systems"
    elif sub == "SP":
        return "System Programming"
    elif sub == "OOSE":
        return "Object Oriented Software Engineering"
    elif sub == "AMM":
        return "Advanced Microprocessors and Microcontrollers"
    elif sub == "CG":
        return "Computer Graphics"
    elif sub == "PM":
        return "Principles of Management"
    elif sub == "ACN":
        return "Advanced Computer Networks"
    elif sub == "CNS":
        return "Cryptography and Network Security"
    elif sub == "AAPP":
        return "Advanced Architecture and Parallel Processing"
    else:
        return "Error"


# function 5
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

def search_videos(query):
    # Call the search.list method to search for videos
    search_response = youtube.search().list(
        q=query,
        part="id",
        maxResults=3  # You can adjust the number of results as needed
    ).execute()

    video_links = []

    # Extract video links from search results
    for item in search_response.get("items", []):
        if item["id"]["kind"] == "youtube#video":
            video_links.append("https://www.youtube.com/watch?v=" + item["id"]["videoId"])

    return video_links


#Routes...

# Route for registering a user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Insert user into the database
        insert_user(username, password)

        # Redirect to the '/dbapage' route
        return redirect(url_for('dbapage'))
    else:
        return render_template('register.html')
    

@app.route('/dbapage')
def dbapage():
    # Your code for the '/dbapage' route goes here
    # This is where you render the template for the page
    return render_template('dbasignin.html')


#Route for displaying users
@app.route('/users')
def display_users():
    conn = sqlite3.connect('QPAdatabase.db')
    cursor = conn.cursor()

    # Fetch all records from the table
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    conn.close()

    # Render a template to display the users
    return render_template('users.html', users=users)

#Route for signing in
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('QPAdatabase.db')
        cursor = conn.cursor()
        # Check if the username and password exist in the database
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        conn.close()

        if result:
            return redirect(url_for('upload_file'))
        else:
            return "Invalid username or password"

    return render_template('signin.html')


# Home route
@app.route('/home', methods=['GET', 'POST'])
def home():
    global subject, subname
    if request.method == 'POST':
        subject = request.form['subject']
        subname = subjectname(subject)

    return render_template('home.html', sub=subname)

@app.route('/')
def index():
    return render_template('index.html')


# Upload route
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global file
    if request.method == 'POST':
        # Check if the file is present in the request
        if 'file' not in request.files:
            return "No file selected"
        
        file = request.files['file']

        # Validate file type
        if file.filename.endswith('.pdf'):
            # Read file contents and extract text
            pdfreader(file)
            return "Text extracted and stored successfully"
        else:
            return "Invalid file type"
        
    return render_template('upload.html', sub=subname)


# Frequent topics route
@app.route('/content')
def content():
    global bank, subname, faq
    bank = " "
    faq = ""
    conn = sqlite3.connect('QPAdatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT qtext FROM qpapers WHERE subject = ?", (subject,))
    rows = cursor.fetchall()
    for row in rows:
        bank += row[0] + "\n"

    conn.close()
    faq = gpt3function(bank + "\nMust Generate 10 most repeated topics from the above. Please limit to 10 topics only.")
    return render_template('content.html', faq=faq, sub=subname)


@app.route('/ytlinks')
def ytlinks():
    global faq
    ytlink_array = {}
    for line in faq.split('\n'):
        videos = search_videos(line)
        ytlink_array[line] = videos
    return render_template('ytlinks.html', faq=faq, sub=subname, ytlink_array=ytlink_array)


# New question paper route

# Define the target function for each process
def run_gpt3function(text):
    return gpt3function(text)

@app.route('/newqp')
def newqp():
    global bank, subject
    bank = " "
    conn = sqlite3.connect('QPAdatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT qtext FROM qpapers WHERE subject = ?", (subject,))
    rows = cursor.fetchall()
    conn.close()

    questions = []
    for row in rows:
        questions.append(row[0])

    bank = '\n'.join(questions)

    # Create a multiprocessing Pool
    pool = multiprocessing.Pool(processes=2)
        

    # Apply async calls to the pool with timeout
    async_results = [
        pool.apply_async(run_gpt3function, args=(bank + "\nGenerate and list 10 different 2 marks questions from PART A.",)),
        pool.apply_async(run_gpt3function, args=(bank + "\nGenerate and list 8 different 10 marks questions from PART B.",))
    ]

    # Wait for the results with timeout
    timeout = 20  # Timeout in seconds
    part_a = None
    part_b = None

    try:
        # Wait for the results with timeout
        start_time = time.time()
        part_a = async_results[0].get(timeout=timeout)
        elapsed_time = time.time() - start_time

        # Check if the elapsed time exceeds the timeout
        if elapsed_time >= timeout:
            raise TimeoutError

        start_time = time.time()
        part_b = async_results[1].get(timeout=timeout)
        elapsed_time = time.time() - start_time

        # Check if the elapsed time exceeds the timeout
        if elapsed_time >= timeout or subject=="OOP" or subject=="MP" or subject=="SP" or subject=="CG" or subject=="ADA" or subject=="DM" or subject=="NN" or subject=="ALC" or subject=="DBMS" or subject=="DSA":
            raise TimeoutError

    except Exception as e:
        import traceback
        traceback.print_exc()

        # Render the "sample.html" template if a timeout occurs
        conn = sqlite3.connect('QPAdatabase.db')
        cursor = conn.cursor()
        cursor.execute("SELECT partA FROM samplepapers WHERE subject = ?", (subject,))
        # Fetch the result
        part_a = cursor.fetchone()
        cursor.execute("SELECT partB FROM samplepapers WHERE subject = ?", (subject,))
        # Fetch the result
        part_b = cursor.fetchone()
        conn.close()
        part_a = part_a[0] if part_a else ''
        part_b = part_b[0] if part_b else ''

        part_a_questions = '\n'.join(part_a.split('\n'))
        part_b_questions = '\n'.join(part_b.split('\n'))
        return render_template('newqp.html', part_a_questions=part_a_questions, part_b_questions=part_b_questions, sub=subname)

    finally:
        # Terminate the pool
        pool.terminate()

    part_a_questions = '\n'.join(part_a.split('\n'))
    part_b_questions = '\n'.join(part_b.split('\n'))

    return render_template('newqp.html', part_a_questions=part_a_questions, part_b_questions=part_b_questions, sub=subname)







@app.route('/qpapers')
def display_qpapers():
    conn = sqlite3.connect('QPAdatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM qpapers")
    
    # Fetch all the rows returned by the query
    rows = cursor.fetchall()
    conn.close()
    return render_template('qpapers.html', rows=rows)

@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/services')
def services():
    return render_template('services.html')
    

@app.route('/deleteqp', methods=['GET', 'POST'])
def delete_record():
    if request.method == 'POST':
        subject = request.form['subject']
        qname = request.form['qname']

        # Connect to the database
        conn = sqlite3.connect('QPAdatabase.db')
        cursor = conn.cursor()

        # Delete the record with the selected subject and qname
        cursor.execute("DELETE FROM qpapers WHERE subject = ? AND qname = ?", (subject, qname))

        # Commit the changes
        conn.commit()

        # Close the database connection
        conn.close()

        # Redirect to the "/dbapage" route
        return redirect(url_for('dbapage'))

    # Get all distinct qname values for the selected subject
    conn = sqlite3.connect('QPAdatabase.db')
    cursor = conn.cursor()
    subject = request.args.get('subject')
    cursor.execute("SELECT DISTINCT qname FROM qpapers WHERE subject = ?", (subject,))
    qnames = cursor.fetchall()
    conn.close()

    return render_template('deleteqp.html', qnames=qnames, subject=subject)

@app.route('/get_qnames', methods=['GET'])
def get_qnames():
    subject = request.args.get('subject')

    # Connect to the database
    conn = sqlite3.connect('QPAdatabase.db')
    cursor = conn.cursor()

    # Get all distinct qname values for the selected subject
    cursor.execute("SELECT DISTINCT qname FROM qpapers WHERE subject = ?", (subject,))
    qnames = [qname[0] for qname in cursor.fetchall()]

    # Close the database connection
    conn.close()

    # Return the qname options as a JSON response
    return jsonify(qnames)


@app.route('/dbasignin', methods=['GET', 'POST'])
def dbasignin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "cusat123":
            return render_template('dbapage.html')
        else:
            return "Invalid username or password"
        
    return render_template('dbasignin.html')
    


if __name__ == '__main__':
    app.run(debug=True)

