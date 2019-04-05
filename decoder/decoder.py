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
    parseResult = parse_image(img)
    parseResult['msgid'] = msg['msgid']
    parseResult['chatid'] = msg['chatid']
    parseResult['datakey'] = msg['datakey']
    parseResult['agentname'] = msg['agentname']
    LOG.info(' => ' + json.dumps(parseResult))
    channel.basic_publish('', 'results', json.dumps(parseResult))
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

    channel.queue_declare('decoder')
    channel.basic_consume('decoder', on_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()