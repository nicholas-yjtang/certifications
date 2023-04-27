from dotenv import load_dotenv
from datetime import datetime
import os

# Import namespaces
import azure.cognitiveservices.speech as speech_sdk
from playsound import playsound


def main():
    try:
        global speech_config

        # Get Configuration Settings
        load_dotenv()
        cog_key = os.getenv('COG_SERVICE_KEY')
        cog_region = os.getenv('COG_SERVICE_REGION')
        use_microphone = os.getenv('USE_MICROPHONE')
        use_voice = os.getenv('USE_VOICE')
        use_ssml = os.getenv('USE_SSML')

        # Configure speech service
        speech_config = speech_sdk.SpeechConfig(cog_key, cog_region)
        print('Ready to use speech service in:', speech_config.region)        

        # Get spoken input
        command = TranscribeCommand(use_microphone)
        if command.lower() == 'what time is it?':
            TellTime(use_voice, use_ssml)

    except Exception as ex:
        print(ex)

def TranscribeCommand(use_microphone):
    command = ''
    speech_recognizer = None
    # Configure speech recognition
    if (use_microphone == 'True'):
        print ('Using microphone...')
        audio_config = speech_sdk.AudioConfig(use_default_microphone=True)
        speech_recognizer = speech_sdk.SpeechRecognizer(speech_config, audio_config)
        print('Speak now...')
    else:
        print('Using audio file...')
        audioFile = 'time.wav'
        playsound(audioFile)
        audio_config = speech_sdk.AudioConfig(filename=audioFile)
        speech_recognizer = speech_sdk.SpeechRecognizer(speech_config, audio_config)


    # Process speech input
    print('Processing speech input...')
    speech = speech_recognizer.recognize_once_async().get()
    if speech.reason == speech_sdk.ResultReason.RecognizedSpeech:
        command = speech.text
        print(command)
    else:
        print(speech.reason)
        if speech.reason == speech_sdk.ResultReason.Canceled:
            cancellation = speech.cancellation_details
            print(cancellation.reason)
            print(cancellation.error_details)

    # Return the command
    return command


def TellTime(use_voice, use_ssml):
    now = datetime.now()
    response_text = 'The time is {}:{:02d}'.format(now.hour,now.minute)
    voice = None

    # Configure speech synthesis
    if (use_voice == 'Ryan'):
        print('Using Ryan voice...')
        voice = 'Ryan'
        speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"
    else:
        print('Using Libby voice...')
        voice = 'Libby'
        speech_config.speech_synthesis_voice_name = 'en-GB-LibbyNeural' # change this

    speech_synthesizer = speech_sdk.SpeechSynthesizer(speech_config)    

    # Synthesize spoken output
    speak = None
    if (use_ssml == 'True'):
        print('Using SSML...')
        responseSsml = " \
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'> \
            <voice name='en-GB-" + voice + "Neural'> \
                {} \
                <break strength='weak'/> \
                Time to end this lab! \
            </voice> \
        </speak>".format(response_text)
        speak = speech_synthesizer.speak_ssml_async(responseSsml).get()
    else:
        print('Using plain text...')
        speak = speech_synthesizer.speak_text_async(response_text).get()

    if speak.reason != speech_sdk.ResultReason.SynthesizingAudioCompleted:
        print(speak.reason)

    # Print the response
    print(response_text)


if __name__ == "__main__":
    main()