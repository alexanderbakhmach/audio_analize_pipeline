from watson_developer_cloud import SpeechToTextV1, TextToSpeechV1
from watson_developer_cloud.websocket import RecognizeCallback, AudioSource, SynthesizeCallback
from sources.tools import ProcessService


class IbmSttService(ProcessService, RecognizeCallback):
    """Implementation of ProcessService and RecognizeCallback

    Realization of ProcessService for IBM speech-to-text
    Also implement IBM Recognize callback it is makes possible to
    use IBM python sdk via web-sockets but with encapsulation of working
    natively with them. More info about how to work with IBM speech-to-text
    sdk can be found in official docs (https://cloud.ibm.com/apidocs/speech-to-text?language=python#websocket_methods)
    or examples in open github repo (https://github.com/watson-developer-cloud/python-sdk/tree/master/examples)

    Attributes:
        url (str): The IBM API url can be found in service credentials of stt service
        key (str): The IBM API key can be found in service credentials of stt service
        interface (SpeechToTextV1): The IBM speech-to-text service instance (see docs)
        input_buffer (Queue): See inherited ProcessService
        output_buffer (Queue): See inherited ProcessService

    """

    SAMPLE_RATE = 44100  # The sample rate of input audio in future will be pass as meta on socket connection
    REQUEST_ENCODING = 'audio/l16'  # The encoding of input audio data

    def __init__(self, key, url):
        """Call super constructors and auth to IBM sdk by creating sdk stt interface

        Args:
            url (str): The IBM API url can be found in service credentials of stt service
            key (str): The IBM API key can be found in service credentials of stt service

        """
        ProcessService.__init__(self)
        RecognizeCallback.__init__(self)
        self.url = url
        self.key = key
        self.interface = SpeechToTextV1(iam_apikey=self.key, url=self.url)

    def act(self):
        """Realization of implemented act() method of ProcessService

        Create the sdk audio source buffer base on input_buffer
        then pass it as argument to stt service handler that
        listen data appearing in buffer and than after recognition
        process finished call callback on_transcription method and
        pass the recognized text there.

        Returns:
            None

        """
        audio_source = AudioSource(self.input_buffer, True, True)
        self.interface.recognize_using_websocket(audio=audio_source,
                                                 content_type=f'{self.REQUEST_ENCODING}; rate={self.SAMPLE_RATE}',
                                                 recognize_callback=self,
                                                 interim_results=True)

    def on_transcription(self, transcript):
        """ Call if some data was recognized by ibm stt service

        Attr:
            transcript (dict): dict contain transcription of recognized text

        Returns:
            None

        """
        message = self.receive_transcript(transcript)
        self.output_buffer.put(message)

    @staticmethod
    def receive_transcript(transcript):
        """Receive the most possible recognition

            Args:
                transcript (dict): dict contain transcription of recognized text

            Returns:
                str

        """
        return transcript[0].get('transcript')


class IbmTtsService(ProcessService, SynthesizeCallback):
    """Implementation of ProcessService and SynthesizeCallback

    Realization of ProcessService for IBM text-to-speech
    Also implement IBM synthesize callback it is makes possible to
    use IBM python sdk via web-sockets but with encapsulation of working
    natively with them. More info about how to work with IBM text-to-speech
    sdk can be found in official docs (https://cloud.ibm.com/apidocs/text-to-speech?language=python#websocket_methods)
    or examples in open github repo (https://github.com/watson-developer-cloud/python-sdk/tree/master/examples)

    Attributes:
        url (str): The IBM API url can be found in service credentials of stt service
        key (str): The IBM API key can be found in service credentials of stt service
        interface (TextToSpeechV1): The IBM speech-to-text service instance (see docs)
        input_buffer (Queue): See inherited ProcessService
        output_buffer (Queue): See inherited ProcessService

    """

    VOICE = 'en-US_AllisonVoice'
    RESPONSE_ENCODING = 'audio/wav'

    def __init__(self, key, url):
        """Call super constructors and auth to IBM sdk by creating sdk stt interface

        Args:
            url (str): The IBM API url can be found in service credentials of stt service
            key (str): The IBM API key can be found in service credentials of stt service

        """
        ProcessService.__init__(self)
        SynthesizeCallback.__init__(self)
        self.url = url
        self.key = key
        self.interface = TextToSpeechV1(iam_apikey=self.key, url=self.url)

    def act(self):
        """Realization of implemented act() method of ProcessService

        In infinitive loop await recognized text from input_buffer
        then pass it to tts service with on result data pass them to
        on_audio_stream callback

        Returns:
            None

        """
        while True:
            text = self.input_buffer.get()
            self.interface.synthesize_using_websocket(text=text,
                                                      synthesize_callback=self,
                                                      accept=f'{self.RESPONSE_ENCODING}',
                                                      voice=f'{self.VOICE}')

    def on_audio_stream(self, audio_data):
        """ Write final created audio to output buffer

        Args:
            audio_data (bytes): The bytes of synthesised recognized text

        Returns:
            None

        """
        self.output_buffer.put(audio_data)


class AnswerService(ProcessService):
    """Represent the bot that answer for recognized text

       Receive some recognized text on input_buffer then pass
       them to bot server and write the bot server response text to
       output buffer for future synthesise

    """
    def __init__(self):
        super().__init__()

    def act(self):
        while True:
            text = self.input_buffer.get()
            self.output_buffer.put(text)
