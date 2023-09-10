import audioop
import base64
import json
import os
from flask import Flask, request, session
from flask_sock import Sock, ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start
from twilio.rest import Client
import vosk
import time
import socket

# app_tutorial_vosk.py
app = Flask(__name__)
sock = Sock(app)
account_sid = ''
auth_token = ''
twilio_client = Client(account_sid, auth_token)
model = vosk.Model('model')

CL = '\x1b[0K'
BS = '\x08'

TRANSCRIPTION_DIR = "transcriptions"

def store_transcription(caller, text):
    with open(os.path.join(TRANSCRIPTION_DIR, caller + ".txt"), "w") as file:
        textArray = text.split(" ")
        if (len(textArray) >= 5 and "thank you" in text):
            if "Response: " in text:
                text = text.split("Response: ")[1]
            print("writing...", text)
            file.write(text)




def retrieve_transcription(caller):
    time.sleep(6)
    try:
        # with open(os.path.join(TRANSCRIPTION_DIR, caller + ".txt"), "r") as file:
        #     return file.read()
        # found_keyword = False
        # content = ""
        # while not found_keyword:
        #     with open("transcriptions/business.txt", 'r') as file:
        #         content = file.read()
        #         if "!!!!!" in content:
        #             found_keyword = True
        with open("transcriptions/business.txt", 'r') as file:
            lines = file.readlines()

        last_line = lines[-1]
        if "Response: " in last_line:
            last_line = last_line.split("Response: ")[1]
                    # open("transcriptions/business.txt", 'w')
        return last_line
    except FileNotFoundError:
        return None

#Route to first run call route and then playback route
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming phone calls"""
    print("voice")
    response = VoiceResponse()
    response.play('https://audio.jukehost.co.uk/JK5gyBq7qNDgl9VdBfRucyy1YURdch1t')
    response.redirect(url='/call')

    return str(response)

#Route to output the transcribed text
@app.route("/playback", methods=['GET', 'POST'])
def playback():
    """Generate response with the transcribed text."""

    print("**************************")
    response = VoiceResponse()
    transcribed = retrieve_transcription("business")
    # with open("transcriptions/business.txt", 'w') as file:
    #     file.write("")
    print("saying...", transcribed)
    response.say(transcribed or "Sorry, I couldn't understand that.", voice='Google.en-US-Neural2-C')
    response.redirect(url='/call')

    return str(response)

@app.route('/call', methods=['POST'])
def call():
    """Accept a phone call."""
    start = Start()
    start.stream(url=f'wss://{request.host}/stream')

    response = VoiceResponse()


    response.append(start)
    response.pause(length=6)
    response.redirect(url='/playback')

    print(f'Incoming call from {request.form["From"]}')
    return str(response), 200, {'Content-Type': 'text/xml'}


@sock.route('/stream')
def stream(ws):
    """Receive and transcribe audio stream."""

    rec = vosk.KaldiRecognizer(model, 16000)

    iterations = 0
    while iterations < 10000000000:
        iterations+=1
        # if iterations % 10 == 0:
        #     print(iterations)
        message = ws.receive()
        packet = json.loads(message)
        if packet['event'] == 'start':
            print('Streaming is starting')
        elif packet['event'] == 'stop':
            print('\nStreaming has stopped')
        elif packet['event'] == 'media':
            audio = base64.b64decode(packet['media']['payload'])
            audio = audioop.ulaw2lin(audio, 2)
            audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
            if rec.AcceptWaveform(audio):
                r = json.loads(rec.Result())
                if (len(r['text']) > 1):
                    print(CL + r['text'] + ' ', end='', flush=True)
                    store_transcription("customer", r['text'])
            else:
                r = json.loads(rec.PartialResult())
                if (len(r['partial']) > 1):
                    print(CL + r['partial'] + BS * len(r['partial']), end='', flush=True)
                    store_transcription("customer", r['partial'])



if __name__ == '__main__':
    from pyngrok import ngrok
    port = 5000
    public_url = ngrok.connect(port, bind_tls=True).public_url
    number = twilio_client.incoming_phone_numbers.list()[0]
    number.update(voice_url=public_url + '/voice')
    print(f'Waiting for calls on {number.phone_number}')

    app.run(port=port)


