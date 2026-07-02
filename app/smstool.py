from config import settings

import time
import threading
import smpplib.client
import smpplib.consts
import smpplib.exceptions

SMSC_HOST = "127.0.0.1"
SMSC_PORT = settings.smpp_port
RETRY_DELAY = 15

client = None
client_lock = threading.Lock()


def decode_message(pdu):
    coding = getattr(pdu, "data_coding", 0)
    try:
        if coding == 0x08:
            return pdu.short_message.decode("utf-16-be")
        else:
            return pdu.short_message.decode("latin-1")
    except Exception:
        return repr(pdu.short_message)


def handle_pdu(pdu):
    if isinstance(pdu, smpplib.command.AlertNotification):
        imsi = pdu.source_addr
        print(f"smpplib.command.AlertNotification from {imsi=}")
        return

    if isinstance(pdu, smpplib.command.DeliverSM):
        text = decode_message(pdu)

        print(f"[SMS] From: {pdu.source_addr.decode()} -> To: {pdu.destination_addr.decode()}")
        print(f"      Text: {text}\n")
        send_sms(f"{pdu.source_addr.decode()}", f"You sent: {text}")
        return

    print(f"[PDU] Unhandled: {pdu.command}")


def connect_and_listen():
    global client
    client = smpplib.client.Client(SMSC_HOST, SMSC_PORT)
    client.set_message_received_handler(handle_pdu)
    try:
        client.connect()
        client.bind_transceiver(
            system_id=settings.smpp_systemid,
            password=settings.smpp_password,
        )
        print(f"Connected to {SMSC_HOST}:{SMSC_PORT} - waiting for messages...\n")
        client.listen()
    finally:
        try:
            client.unbind()
        except Exception:
            pass
        client.disconnect()


def send_sms(dest, text, source="476"):
    with client_lock:
        if client is None or client.state != smpplib.consts.SMPP_CLIENT_STATE_BOUND_TRX:
            raise RuntimeError("SMPP client not connected/bound yet")
        return client.send_message(
            source_addr=source,
            destination_addr=dest,
            short_message=text.encode(),
        )


def main():
    while True:
        try:
            connect_and_listen()
        except smpplib.exceptions.ConnectionError as e:
            print(f"[ERROR] Connection refused - is osmo-msc running and SMPP enabled? ({e})")
        except smpplib.exceptions.PDUError as e:
            print(f"[ERROR] SMPP PDU error: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        print(f"Retrying in {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    main()
