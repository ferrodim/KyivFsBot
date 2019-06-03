import pika
import logging
import json
from PIL import Image
from time import sleep
from image_process import parse_image


def on_message(channel, method_frame, header_frame, body):
    LOG.info(' <= %s', body)
    msg = json.loads(body)
    img = Image.open('/Screens/' + msg['img'])
    try:
        parse_result = parse_image(img)
    except:
        parse_result = {"filename": 'exception', "success": False}
    parse_result['msgid'] = msg['msgid']
    parse_result['chatid'] = msg['chatid']
    parse_result['datakey'] = msg['datakey']
    parse_result['agentname'] = msg['agentname']
    LOG.info(' => ' + json.dumps(parse_result))
    channel.basic_publish('main', 'parseResult', json.dumps(parse_result))
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


if __name__ == '__main__':
    # sleep a few seconds to allow RabbitMQ server to come up
    sleep(3)
    logging.basicConfig(level=logging.INFO)
    LOG = logging.getLogger(__name__)
    credentials = pika.PlainCredentials('rabbitmq', 'rabbitmq')
    parameters = pika.ConnectionParameters("rabbit", 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)

    channel.exchange_declare(exchange='main', exchange_type='direct', durable=True)
    channel.queue_declare(queue='bot', durable=True)
    channel.queue_declare(queue='decoders', durable=True)
    channel.queue_bind('bot', 'main', 'parseResult')
    channel.queue_bind('decoders', 'main', 'parseRequest')

    channel.basic_consume('decoders', on_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()
