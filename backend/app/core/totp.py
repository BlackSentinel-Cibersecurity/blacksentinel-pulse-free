import pyotp
import qrcode
import io
import base64


class TOTPService:
    """TOTP-based 2FA service compatible with Google Authenticator and similar apps."""

    @staticmethod
    def generate_secret() -> str:
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(
        secret: str, email: str, issuer: str = "BlackSentinel Pulse"
    ) -> str:
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)

    @staticmethod
    def generate_qr_code_base64(
        secret: str, email: str, issuer: str = "BlackSentinel Pulse"
    ) -> str:
        uri = TOTPService.get_provisioning_uri(secret, email, issuer)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

    @staticmethod
    def verify(secret: str, token: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    @staticmethod
    def get_current_token(secret: str) -> str:
        totp = pyotp.TOTP(secret)
        return totp.now()


totp_service = TOTPService()
