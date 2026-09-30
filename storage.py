import pika
import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
STORAGE_DIR = os.getenv("STORAGE_DIR", "./data/storage/storage_1")

def main():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    channel.exchange_declare(exchange='storage_fanout', exchange_type='fanout')

    # Fila exclusiva para este no de armazenamento receber todas as mensagens do fanout
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='storage_fanout', queue=queue_name)

    def callback(ch, method, properties, body):
        header, image_data = body.split(b'|', 1)
        filename = header.decode('utf-8')
        
        filepath = os.path.join(STORAGE_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(image_data)

        print(f"[Storage] Imagem redundante salva com sucesso em: {filepath}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    print(f'[Storage] Servidor de armazenamento aguardando imagens em {STORAGE_DIR}...')
    channel.start_consuming()

if __name__ == '__main__':
    main()