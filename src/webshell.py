from flask import Flask, request, jsonify, Response, session, redirect, url_for
import subprocess
import uuid
import os

WEBSHELL_PASSWORD = os.getenv('WEBSHELL_PASSWORD')


def shell_process():
        
    if WEBSHELL_PASSWORD is None:
        raise ValueError('WEBSHELL_PASSWORD environment variable not set')
    
    app = Flask(__name__)
    app.secret_key = uuid.uuid4().hex


    @app.before_request
    def check_auth():
        if request.endpoint in ['shell_interface', 'run_command'] and not session.get('logged_in'):
            return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            if request.form.get('password') == WEBSHELL_PASSWORD:
                session['logged_in'] = True
                return redirect(url_for('shell_interface'))
            return "Invalid password", 403
        return '''
        <html>
        <body>
            <form method="POST">
                <input type="password" name="password" placeholder="Enter password" />
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
        '''

    @app.route('/')
    def index():
        return '''
    <html>
    <head>
    </head>
    <body>
    Go to <a href="/shell">/shell</a>
    </body>
    </html>
    '''

    @app.route('/shell')
    def shell_interface():
        return """
        <html>
        <head>
            <style>
                body {
                    background-color: #222;
                    color: #eee;
                    margin: 0;
                    font-family: monospace;
                }
                #chat-container {
                    height: 80vh;
                    overflow-y: auto;
                    padding: 10px;
                    border-bottom: 1px solid #555;
                }
                #input-container {
                    display: flex;
                    padding: 10px;
                }
                #command {
                    flex: 1;
                    background-color: #333;
                    border: 1px solid #555;
                    color: #eee;
                    padding: 5px;
                }
                #sendBtn {
                    background-color: #444;
                    color: #eee;
                    border: none;
                    padding: 6px 12px;
                    margin-left: 5px;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <div id="chat-container"></div>
            <div id="input-container">
                <input type="text" id="command" placeholder="Enter command" />
                <button id="sendBtn">Send</button>
            </div>
            <script>
                const chatContainer = document.getElementById('chat-container');
                const commandInput = document.getElementById('command');
                const sendBtn = document.getElementById('sendBtn');
                const commandHistory = [];
                let commandIndex = 0;

                function appendMessage(text) {
                    text.split('\\n').forEach(line => {
                        let div = document.createElement('div');
                        div.textContent = line;
                        chatContainer.appendChild(div);
                    });
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }

                function sendCommand() {
                    let cmd = commandInput.value;
                    commandHistory.push(cmd);
                    commandIndex = commandHistory.length;
                    commandInput.value = '';
                    appendMessage("–".repeat(120));
                    appendMessage("> " + cmd);
                    appendMessage("·".repeat(120));
                    const eventSource = new EventSource('/run_command?command=' + encodeURIComponent(cmd));
                    eventSource.onmessage = function(event) {
                        appendMessage(event.data);
                    };
                    eventSource.onerror = function() {
                        eventSource.close();
                    };
                }

                sendBtn.addEventListener('click', sendCommand);
                commandInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        sendCommand();
                    }
                });
                commandInput.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowUp') {
                        commandIndex = Math.max(0, commandIndex-1);
                        commandInput.value = commandHistory[commandIndex] || '';
                    }
                    if (e.key === 'ArrowDown') {
                        commandIndex = Math.min(commandHistory.length, commandIndex+1);
                        commandInput.value = commandHistory[commandIndex] || '';
                    }
                });
            </script>
        </body>
        </html>
        """

    @app.route('/run_command')
    def run_command():
        cmd = request.args.get('command', '')
        if not cmd:
            return Response("No command entered", mimetype='text/plain')
        
        def generate():
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            while process.stdout.readable():
                line = process.stdout.readline()
                if not line:
                    break
                yield f"data: {line}\n\n"
            # process.wait()

        return Response(generate(), mimetype='text/event-stream')
    app.run(debug=False, host='0.0.0.0', port=5001)

# if __name__ == '__main__':
#     shell_process()
