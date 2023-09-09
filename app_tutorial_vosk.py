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

app = Flask(__name__)
sock = Sock(app)
account_sid = 'AC5e69a82ff2fcd6e939928a173c9baf3d'
auth_token = '0c34a01816e0ef3c226e2c67c2fbb8f1'
twilio_client = Client(account_sid, auth_token)
model = vosk.Model('model')

CL = '\x1b[0K'
BS = '\x08'


TRANSCRIPTION_DIR = "transcriptions"

ttext = ""


def store_transcription(caller, text):
    with open(os.path.join(TRANSCRIPTION_DIR, caller + ".txt"), "w") as file:
        if (len(text) > 4):
            print("writing...", text)
        file.write(text)



def retrieve_transcription(caller):
    try:
        with open(os.path.join(TRANSCRIPTION_DIR, caller + ".txt"), "r") as file:
            return file.read()
    except FileNotFoundError:
        return None

#Route to first run call route and then playback route
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming phone calls"""
    response = VoiceResponse()
    response.redirect(url='/call')

    return str(response)

#Route to output the transcribed text
@app.route("/playback", methods=['GET', 'POST'])
def playback():
    """Generate response with the transcribed text."""

    global ttext

    print("**************************")
    response = VoiceResponse()
    transcribed = retrieve_transcription("temp")
    print("saying...", transcribed)
    print("TTEXT: ", ttext)
    # response.say(transcribed or "Sorry, I couldn't understand that.")
    response.say(ttext or "Sorry, I couldn't understand that.")
    return str(response)

@app.route('/call', methods=['POST'])
def call():
    """Accept a phone call."""
    start = Start()
    start.stream(url=f'wss://{request.host}/stream')



    response = VoiceResponse()


    response.append(start)
    response.play('https://audio.jukehost.co.uk/W9WoQPsIRF4BPOLNoU7b2RrqUrWaDHCh')
    response.pause(length=6)
    response.redirect(url='/playback')

    print(f'Incoming call from {request.form["From"]}')
    return str(response), 200, {'Content-Type': 'text/xml'}


@sock.route('/stream')
def stream(ws):
    """Receive and transcribe audio stream."""
    global ttext

    rec = vosk.KaldiRecognizer(model, 16000)

    iterations = 0
    while iterations < 10000000000:
        iterations+=1
        print(iterations)
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
                    # store_transcription("temp", r['text'])
                    ttext = r['text']
            else:
                r = json.loads(rec.PartialResult())
                if (len(r['partial']) > 1):
                    print(CL + r['partial'] + BS * len(r['partial']), end='', flush=True)
                    # store_transcription("temp", r['partial'])
                    ttext = r['partial']



if __name__ == '__main__':
    from pyngrok import ngrok
    port = 5000
    public_url = ngrok.connect(port, bind_tls=True).public_url
    number = twilio_client.incoming_phone_numbers.list()[0]
    number.update(voice_url=public_url + '/voice')
    print(f'Waiting for calls on {number.phone_number}')

    app.run(port=port)