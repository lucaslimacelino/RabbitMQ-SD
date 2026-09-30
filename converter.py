import pika
import os
import io
from PIL import Image

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Declara a fila de entrada das imagens enviadas pelos clientes
    channel.queue_declare(queue='task_queue', durable=True)
    
    # Declara o Exchange do tipo fanout para replicar entre os servidores de armazenamento
    channel.exchange_declare(exchange='storage_fanout', exchange_type='fanout')

    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        header, image_data = body.split(b'|', 1)
        filename = header.decode('utf-8')
        print(f"[Conversor] Processando e convertendo: {filename}")

        # Conversao da imagem para tons de cinza
        img = Image.open(io.BytesIO(image_data))
        gray_img = img.convert('L')
        
        output_buffer = io.BytesIO()
        img_format = img.format if img.format else 'JPEG'
        gray_img.save(output_buffer, format=img_format)
        gray_bytes = output_buffer.getvalue()

        # Publica no Exchange fanout (X) com o mesmo nome original
        payload = filename.encode('utf-8') + b'|' + gray_bytes
        channel.basic_publish(exchange='storage_fanout', routing_key='', body=payload)
        
        print(f"[Conversor] Imagem {filename} convertida com sucesso e enviada ao Exchange.")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='task_queue', on_message_callback=callback)
    print('[Conversor] Servidor pronto. Aguardando imagens...')
    channel.start_consuming()

if __name__ == '__main__':
    main()