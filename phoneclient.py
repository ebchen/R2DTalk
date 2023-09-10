# echo-client.py
import app_tutorial_vosk
import socket

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65434  # The port used by the server
# convo = ["What does dim sum mean?", "Is there bok choi on the menu?", "Is it vegetarian?", "bye"]
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:

        # function call to get user text from phone call
        last_line = ""
        i = 0
        #  send string to the phone server
        while True:
            # query = input("Enter your query: ")
            content = ""
            # Flag to determine if the keyword has been found
            found_keyword = False
            last_line = ""
            # Read the file
            while not found_keyword and len(content) == 0:
                with open("transcriptions/customer.txt", 'r') as file:
                    i += 1
                    if i % 2 == 0:
                        content = file.read()
                        if "thank you" in content:
                            # last_line = content
                            found_keyword = True
                    open("transcriptions/customer.txt", 'w')

            # with open("transcriptions/business.txt", 'r') as file:
            #     lines = file.readlines()
            # if len(lines) > 0 and lines[-1] != last_line:
            #     content = lines[-1]
            #     last_line = content
            #         # open("transcriptions/business.txt", 'w')
            if content != last_line:
                last_line = content
                if "bye" in content:
                    break
                print("left inner loop")
                print("content", content)
                s.sendall(content.encode('utf-8'))

                # print("check1")
                data = s.recv(1024)
                # print("check2")
                text_to_write = data.decode('utf-8')
                # print("check3")

                print("text_to_write:", text_to_write)
                with open("transcriptions/business.txt", 'a') as file:
                    file.write(text_to_write + "\n")

                # modify data to change to voice call
                print(f"{data!r}")

