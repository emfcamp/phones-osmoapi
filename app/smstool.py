from config import settings

import smpplib.client
import smpplib.consts
import smpplib.gsm


def handle_pdu(pdu):
    print(pdu)


def main():
    client = smpplib.client.Client("127.0.0.1", settings.smpp_port)
    client.set_message_received_handler(handle_pdu)

    print(f"Connecting on port:{settings.smpp_port}...")
    client.connect()
    client.bind_receiver(system_id=settings.smpp_systemid, password=settings.smpp_password)
    print("Bound as receiver. Waiting for messages...\n")

    try:
        client.listen()
    except KeyboardInterrupt:
        print("\nDisconnecting...")
    finally:
        client.disconnect()


if __name__ == '__main__':
    main()