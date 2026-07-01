from config import settings

import smpplib.client
import smpplib.consts
import smpplib.gsm
import time


SMSC_HOST = "127.0.0.1"
SMSC_PORT = settings.smpp_port
RETRY_DELAY = 15


def handle_pdu(pdu):
    print(pdu)
    # if isinstance(pdu, smpplib.client.smpplib.smpp.DeliverSM):
    #     try:
    #         Try UCS-2 first, fall back to Latin-1
    #         text = pdu.short_message.decode('utf-16-be')
    #     except UnicodeDecodeError:
    #         text = pdu.short_message.decode('latin-1')

    #     print(f"[SMS] From: {pdu.source_addr.decode()} -> To: {pdu.destination_addr.decode()}")
    #     print(f"      Text: {text}")
    #     print()


def connect_and_listen():
    client = smpplib.client.Client(SMSC_HOST, SMSC_PORT)
    client.set_message_received_handler(handle_pdu)
    try:
        client.connect()
        client.bind_receiver(system_id=settings.smpp_systemid, password=settings.smpp_password)
        print(f"Connected to {SMSC_HOST}:{SMSC_PORT} — waiting for messages...\n")
        client.listen()
    finally:
        client.disconnect()


def main():
    while True:
        try:
            connect_and_listen()
        except smpplib.exceptions.ConnectionError as e:
            print(f"[ERROR] Connection refused — is osmo-msc running and SMPP enabled? ({e})")
            print(f"        Retrying in {RETRY_DELAY}s...")
        except smpplib.exceptions.PDUError as e:
            print(f"[ERROR] SMPP PDU error (wrong system_id/password?): {e}")
            print(f"        Retrying in {RETRY_DELAY}s...")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            print(f"        Retrying in {RETRY_DELAY}s...")
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    main()
