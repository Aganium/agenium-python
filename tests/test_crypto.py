"""Tests for crypto module."""

from agenium.crypto.keys import KeyPair, generate_keypair


class TestKeyGeneration:
    def test_generate(self):
        kp = generate_keypair()
        assert isinstance(kp, KeyPair)
        assert kp.public_key_b64
        assert len(kp.public_key_b64) == 44  # 32 bytes base64

    def test_sign_verify(self):
        kp = generate_keypair()
        data = b"hello agenium"
        sig = kp.sign(data)
        assert kp.verify(sig, data) is True

    def test_verify_wrong_data(self):
        kp = generate_keypair()
        sig = kp.sign(b"original")
        assert kp.verify(sig, b"tampered") is False

    def test_pem_export(self):
        kp = generate_keypair()
        assert kp.private_key_pem().startswith("-----BEGIN PRIVATE KEY-----")
        assert kp.public_key_pem().startswith("-----BEGIN PUBLIC KEY-----")

    def test_unique_keys(self):
        k1 = generate_keypair()
        k2 = generate_keypair()
        assert k1.public_key_b64 != k2.public_key_b64
