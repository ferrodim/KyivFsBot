import pika
import logging
import json
import base64
from PIL import Image
from time import sleep
from io import BytesIO
from image_process import parse_image


def _(msg):
    return msg


def on_message(channel, method_frame, header_frame, body):
    LOG.info(' <= %s', body)
    msg = json.loads(body)
    if msg['event'] == 'core.messageIn':
        if msg['text'] == '/ping':
            send_localized_text(channel, _('Pong from %s'), msg['chatid'], ['decoder'])
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        return
    send_localized_text(channel, _('Image retrieved'), msg['chatid'])
    img = Image.open(BytesIO(base64.b64decode(msg['raw_img'])))
    # img = Image.open('/Screens/' + msg['img'])
    try:
        parse_result = parse_image(img, '')
    except Exception as e:
        LOG.error('Exception', exc_info=e)
        parse_result = {"filename": 'exception', "success": False}
    parse_result['msgid'] = msg['msgid']
    parse_result['chatid'] = msg['chatid']
    # parse_result['datakey'] = msg['datakey']
    parse_result['tg_name'] = msg['tg_name']
    rabbit_send(channel, parse_result)
    # TODO: send parse_result to "store"
    # LOG.info(' => ' + json.dumps(parse_result))
    # channel.basic_publish('topic', 'parseResult', json.dumps(parse_result))
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def send_localized_text(ch, text, chatid, placeholders = None):
    query = {
        "event": 'call.translateAndSend',
        "args": {
            "chatId": chatid,
            "text": text,
            "placeholders": placeholders,
        }
    }
    rabbit_send(ch, query)


def rabbit_send(ch, ev):
    msg_str = json.dumps(ev)
    LOG.info('{Rabbit} => %s', msg_str)
    route = ev['event'] if "event" in ev else 'parseResult'
    ch.basic_publish('topic', route, msg_str)


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

    channel.exchange_declare(exchange='topic', exchange_type='topic', durable=True)
    channel.queue_declare(queue='decoders', durable=True)
    channel.queue_bind('decoders', 'topic', 'parseRequest')
    channel.queue_bind('decoders', 'topic', 'core.messageIn')
    channel.queue_bind('decoders', 'topic', 'core.photoIn')

    channel.basic_consume('decoders', on_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()
