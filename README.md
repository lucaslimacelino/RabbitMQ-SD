# Aluno:Lucas Lima Celino

# Módulo de Conversão e Armazenamento Redundante de Imagens — DCompany

Este repositório contém a solução desenvolvida para a avaliação da disciplina de **Sistemas Distribuídos** da **Universidade Federal de Sergipe (UFS)**.

O sistema utiliza uma arquitetura baseada em **filas de mensagens com RabbitMQ** para realizar o processamento assíncrono e distribuído de imagens. As imagens são convertidas para **escala de cinza** e, posteriormente, armazenadas de forma **redundante em dois servidores de armazenamento**, garantindo que cada imagem processada possua duas cópias.

---

##  Arquitetura da Solução

A solução foi desenvolvida seguindo a arquitetura proposta na atividade.

O fluxo de processamento pode ser representado da seguinte forma:

```text
                 ┌─────────────────┐
                 │    Cliente 1    │
                 │   (client.py)   │
                 └────────┬────────┘
                          │
                          │
                 ┌────────▼────────┐
                 │                 │
                 │   RabbitMQ      │
                 │   task_queue    │
                 │                 │
                 └────────┬────────┘
                          │
                 ┌────────┴────────┐
                 │                 │
          ┌──────▼──────┐   ┌──────▼──────┐
          │ Conversor C1│   │ Conversor C2│
          │ converter.py│   │ converter.py│
          └──────┬──────┘   └──────┬──────┘
                 │                 │
                 └────────┬────────┘
                          │
                          ▼
                ┌───────────────────┐
                │  Fanout Exchange  │
                │ storage_fanout    │
                └─────────┬─────────┘
                          │
                 ┌────────┴────────┐
                 │                 │
          ┌──────▼──────┐   ┌──────▼──────┐
          │  Storage C3  │   │  Storage C4 │
          │ storage.py   │   │ storage.py  │
          └──────┬──────┘   └──────┬──────┘
                 │                 │
                 ▼                 ▼
          ┌─────────────┐   ┌─────────────┐
          │  storage_1  │   │  storage_2  │
          └─────────────┘   └─────────────┘
```

### Componentes

**1. Produtores (Clientes)**

As instâncias de `client.py` atuam como produtores. Cada cliente lê as imagens presentes em seu respectivo diretório de entrada:

```text
data/input/input_1/
data/input/input_2/
```

Para cada imagem, o cliente envia uma mensagem para o RabbitMQ contendo:

* Nome original da imagem;
* Dados binários da imagem.

---

**2. Fila de tarefas — `task_queue`**

As mensagens enviadas pelos clientes são armazenadas na fila `task_queue`.

A fila permite que o processamento seja realizado de forma **assíncrona**, desacoplando os clientes dos servidores responsáveis pela conversão.

---

**3. Servidores de Conversão — C1 e C2**

Duas instâncias de `converter.py` atuam como consumidores da `task_queue`.

```text
C1 ──┐
     ├──> task_queue
C2 ──┘
```

O RabbitMQ distribui as tarefas entre os consumidores utilizando seu mecanismo de balanceamento, permitindo que as imagens sejam processadas de forma distribuída.

Cada conversor:

1. Recebe uma imagem da fila;
2. Decodifica os dados recebidos;
3. Utiliza a biblioteca **Pillow** para realizar a conversão;
4. Converte a imagem para escala de cinza;
5. Publica o resultado no exchange `storage_fanout`.

---

**4. Exchange Fanout — `storage_fanout`**

Após a conversão, a imagem não é enviada diretamente para um único servidor.

Ela é publicada no exchange:

```text
storage_fanout
```

Esse exchange utiliza o tipo **fanout**, fazendo com que cada mensagem publicada seja encaminhada para **todas as filas conectadas a ele**.

---

**5. Servidores de Armazenamento — C3 e C4**

Cada servidor de armazenamento executa uma instância de `storage.py` e possui sua própria fila conectada ao exchange `storage_fanout`.

```text
                    storage_fanout
                    /            \
                   /              \
            storage_queue_1   storage_queue_2
                  │                 │
                  ▼                 ▼
             Storage C3        Storage C4
                  │                 │
                  ▼                 ▼
             storage_1          storage_2
```

Dessa forma, **todas as imagens convertidas são enviadas para os dois servidores de armazenamento**.

Isso garante a redundância dos dados:

```text
Imagem convertida
       │
       ├──────────> storage_1/
       │
       └──────────> storage_2/
```

Os arquivos são armazenados mantendo seus **nomes originais**.

---

##  Tecnologias Utilizadas

* **Python 3.10**
* **RabbitMQ 3**
* **Pika** — comunicação entre Python e RabbitMQ
* **Pillow** — processamento e conversão das imagens
* **Docker**
* **Docker Compose**

O RabbitMQ também possui o **Management Plugin** habilitado para permitir o acompanhamento visual das filas, consumidores e exchanges.

---



### Descrição dos principais arquivos

| Arquivo              | Função                                                        |
| -------------------- | ------------------------------------------------------------- |
| `client.py`          | Lê as imagens e publica as tarefas no RabbitMQ                |
| `converter.py`       | Consome as tarefas e converte as imagens para escala de cinza |
| `storage.py`         | Consome as imagens convertidas e realiza o armazenamento      |
| `docker-compose.yml` | Define e orquestra os containers da aplicação                 |
| `Dockerfile`         | Define a imagem Docker utilizada pelos serviços Python        |
| `requirements.txt`   | Lista as dependências Python do projeto                       |

---

#  Tutorial de Execução

## Pré-requisitos

Antes de executar o projeto, certifique-se de possuir:

 **Docker Desktop** instalado;
 **Git** instalado;
 Docker Desktop em execução.

---

## 1. Clonar o Repositório

Abra um terminal e execute:

```bash
git clone https://github.com/lucaslimacelino/RabbitMQ-SD.git
```

Entre na pasta do projeto:

```bash
cd RabbitMQ-SD
```



---

## 2. Verificar as Imagens de Entrada

Certifique-se de que existem imagens nos diretórios:

```text
data/input/input_1/
data/input/input_2/
```

São aceitas imagens nos formatos utilizados pelo projeto, como:

```text
.jpg
.png
```

As imagens presentes nesses diretórios serão utilizadas pelos clientes como entrada do sistema.

---

## 3. Subir o Ambiente Docker

Na raiz do projeto, execute:

```bash
docker-compose up --build
```

O comando irá:

1. Construir a imagem Docker da aplicação;
2. Criar os containers definidos no `docker-compose.yml`;
3. Inicializar o RabbitMQ;
4. Inicializar os clientes;
5. Inicializar os servidores de conversão;
6. Inicializar os servidores de armazenamento;
7. Iniciar o fluxo de processamento das imagens.

---

##  Como Validar os Resultados

### 1. Verificar os Logs

Durante a execução, os logs dos containers apresentarão as etapas do processamento.

O fluxo esperado é semelhante a:

```text
Cliente
   ↓
Envio da imagem
   ↓
task_queue
   ↓
Conversor C1/C2
   ↓
Conversão para escala de cinza
   ↓
storage_fanout
   ↓
Storage C3/C4
   ↓
storage_1 + storage_2
```

Os logs permitem verificar se cada etapa foi executada corretamente.

---

### 2. Verificar os Arquivos Armazenados

Após o processamento, verifique os diretórios:

```text
data/storage/storage_1/
data/storage/storage_2/
```

As duas pastas devem conter as imagens processadas.

Por exemplo:

```text
storage_1/
├── imagem1.jpg
├── imagem2.png
└── imagem3.jpg

storage_2/
├── imagem1.jpg
├── imagem2.png
└── imagem3.jpg
```

As imagens devem:

 Estar convertidas para escala de cinza;
 Manter os nomes originais;
 Estar presentes nos dois diretórios de armazenamento.

---

## 3. Acessar o RabbitMQ Management

O RabbitMQ disponibiliza uma interface web para acompanhar o funcionamento do sistema.

Com os containers em execução, acesse:

```text
http://localhost:15672
```

Utilize as credenciais padrão:

```text
Usuário: guest
Senha: guest
```

No painel é possível acompanhar informações como:

 Filas;
 Mensagens;
 Consumidores;
 Exchanges;
 Conexões;
 Taxa de publicação e consumo.

Também é possível visualizar o fluxo relacionado ao exchange:

```text
storage_fanout
```

e suas filas de armazenamento.

---


