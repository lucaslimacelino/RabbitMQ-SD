import sys
import os
import pika

INPUT_DIR = os.getenv("INPUT_DIR", "./data/input/input_1")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    if not os.path.exists(INPUT_DIR):
        print(f"[Cliente] Diretorio {INPUT_DIR} nao encontrado.")
        return

    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f)) and not f.startswith('.')]
    
    if not files:
        print(f"[Cliente] Nenhuma imagem encontrada em {INPUT_DIR}")
        return

    for filename in files:
        filepath = os.path.join(INPUT_DIR, filename)
        with open(filepath, 'rb') as f:
            image_bytes = f.read()
        
        # Estrutura do payload: nome_do_arquivo|bytes_da_imagem
        payload = filename.encode('utf-8') + b'|' + image_bytes

        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=payload,
            properties=pika.BasicProperties(delivery_mode=2) # Mensagem persistente
        )
        print(f"[Cliente] Imagem enviada: {filename}")

    connection.close()

if __name__ == '__main__':
    main()