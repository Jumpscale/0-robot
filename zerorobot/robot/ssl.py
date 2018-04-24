from os.path import exists, join
from socket import gethostname

from OpenSSL import crypto

CERT_FILE = "zrobot.crt"
KEY_FILE = "zrobot.key"


def create_self_signed_cert(cert_dir):
    """
    If datacard.crt and datacard.key don't exist in cert_dir, create a new
    self-signed cert and keypair and write them into that directory.
    """

    if not exists(join(cert_dir, CERT_FILE)) \
            or not exists(join(cert_dir, KEY_FILE)):

        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        # create a self-signed cert
        cert = crypto.X509()
        # cert.get_subject().C = "US"
        # cert.get_subject().ST = "Minnesota"
        # cert.get_subject().L = "Minnetonka"
        cert.get_subject().O = "GIG"
        cert.get_subject().OU = "0-OS"
        cert.get_subject().CN = gethostname()
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)  # 10 years
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')

        cert_path = join(cert_dir, CERT_FILE)
        key_path = join(cert_dir, KEY_FILE)
        open(cert_path, "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(key_path, "wb").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

        return (cert_path, key_path)
