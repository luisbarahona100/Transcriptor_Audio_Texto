import asyncio
import sounddevice as sd
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

# Variable para almacenar el texto transcrito
texto_transcrito = ""

class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ultimo_transcrito = ""

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                self.ultimo_transcrito = alt.transcript

    def get_transcrito(self):
        return self.ultimo_transcrito

async def mic_stream(duration):
    loop = asyncio.get_event_loop()
    input_queue = asyncio.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status, flush=True)
        loop.call_soon_threadsafe(input_queue.put_nowait, (bytes(indata), status))

    try:
        stream = sd.RawInputStream(
            channels=1,
            samplerate= 16000,  # Cambiado a 8000 Hz
            callback=callback,
            blocksize=1024 * 2,
            dtype="int16",
        )

        with stream:
            end_time = loop.time() + duration
            while loop.time() < end_time:
                indata, status = await input_queue.get()
                yield indata, status

    except Exception as e:
        print(f"Error in mic_stream: {e}", flush=True)

async def write_chunks(stream, duration):
    try:
        async for chunk, status in mic_stream(duration):
            await stream.input_stream.send_audio_event(audio_chunk=chunk)
        await stream.input_stream.end_stream()
    except Exception as e:
        print(f"Error in write_chunks: {e}", flush=True)

async def transcribir_audio(): #CADA VEZ QUE SE LLAMA A ESTA FUNCIÓN SE REALIZA LA TRANSCRICIÓN DE AUDIOESPAÑOL A TEXTO
    global texto_transcrito
    try:
        client = TranscribeStreamingClient(region="us-east-2")
        stream = await client.start_stream_transcription(
            language_code="es-US",  # Cambiado a español (España)
            media_sample_rate_hz= 16000,  # Cambiado a 8000 Hz
            media_encoding="pcm"
        )

        handler = MyEventHandler(stream.output_stream)

        await asyncio.gather(write_chunks(stream, 5), handler.handle_events()) ##ENTREGAR O DURACCIÓN DE TRANSCRIPCIÓN (5 SEGUNDOS)

        # Almacenar el último texto transcrito en la variable global
        texto_transcrito = handler.get_transcrito()
        # Imprimir el último texto transcrito en la consola
        print("Texto transcrito:", texto_transcrito)
    except Exception as e:
        print(f"Error in transcribir_audio: {e}", flush=True)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()

        async def main():
            await transcribir_audio()

        loop.run_until_complete(main())
        loop.close()
    except Exception as e:
        print(f"Error in main: {e}", flush=True)
