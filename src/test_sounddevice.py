import sounddevice as sd

def callback(indata, frames, time, status):
    print(indata)

stream = sd.RawInputStream(callback=callback)
with stream:
    sd.sleep(5000)

#Esto debería imprimir matrices de datos de audio a la consola. Si esto no funciona, es posible que haya un problema con tu dispositivo de audio o con la configuración de sounddevice.

#FUNCIONA CORRECTAMENTE