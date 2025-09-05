from typing import Any, Dict


class EmailTemplates:
    @staticmethod
    def queue_subscription(
        customer_name: str, queue_name: str, position: int, estimated_wait: str
    ) -> Dict[str, str]:
        subject = f"You've joined the queue at {queue_name}"

        text_body = f"""
Hi {customer_name},

You've successfully joined the queue at {queue_name}.

Your current position: #{position}
Estimated wait time: {estimated_wait}

We'll notify you when it's almost your turn. Please make sure you're ready when called.

Thank you for using Sqipit!
        """.strip()

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; }}
        .info-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #4CAF50; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>You've Joined the Queue!</h1>
        </div>
        <div class="content">
            <p>Hi {customer_name},</p>
            <p>You've successfully joined the queue at <strong>{queue_name}</strong>.</p>
            <div class="info-box">
                <p><strong>Your Position:</strong> #{position}</p>
                <p><strong>Estimated Wait Time:</strong> {estimated_wait}</p>
            </div>
            <p>We'll notify you when it's almost your turn. Please make sure you're ready when called.</p>
        </div>
        <div class="footer">
            <p>Thank you for using Sqipit!</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return {"subject": subject, "text_body": text_body, "html_body": html_body}

    @staticmethod
    def next_in_line(
        customer_name: str, queue_name: str, service_location: str
    ) -> Dict[str, str]:
        subject = f"It's your turn at {queue_name}!"

        text_body = f"""
Hi {customer_name},

IT'S YOUR TURN!

You're next in line at {queue_name}.
Please proceed to: {service_location}

If you're not ready, you may lose your spot in the queue.

Thank you for using Sqipit!
        """.strip()

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #FF5722; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; }}
        .alert-box {{ background-color: #FFF3E0; padding: 20px; margin: 15px 0; border: 2px solid #FF5722; text-align: center; }}
        .info-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #FF5722; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
        .urgent {{ color: #FF5722; font-size: 24px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 It's Your Turn!</h1>
        </div>
        <div class="content">
            <p>Hi {customer_name},</p>
            <div class="alert-box">
                <p class="urgent">YOU'RE NEXT IN LINE!</p>
            </div>
            <div class="info-box">
                <p><strong>Location:</strong> {queue_name}</p>
                <p><strong>Proceed to:</strong> {service_location}</p>
            </div>
            <p><strong>Important:</strong> If you're not ready, you may lose your spot in the queue.</p>
        </div>
        <div class="footer">
            <p>Thank you for using Sqipit!</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return {"subject": subject, "text_body": text_body, "html_body": html_body}

    @staticmethod
    def almost_your_turn(
        customer_name: str, queue_name: str, position: int, estimated_wait: str
    ) -> Dict[str, str]:
        subject = f"Almost your turn at {queue_name}"

        text_body = f"""
Hi {customer_name},

You're almost up at {queue_name}!

Your current position: #{position}
Estimated wait time: {estimated_wait}

Please start making your way to the location so you're ready when called.

Thank you for using Sqipit!
        """.strip()

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #FFC107; color: #333; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; }}
        .info-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #FFC107; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Almost Your Turn!</h1>
        </div>
        <div class="content">
            <p>Hi {customer_name},</p>
            <p>You're almost up at <strong>{queue_name}</strong>!</p>
            <div class="info-box">
                <p><strong>Your Position:</strong> #{position}</p>
                <p><strong>Estimated Wait Time:</strong> {estimated_wait}</p>
            </div>
            <p>Please start making your way to the location so you're ready when called.</p>
        </div>
        <div class="footer">
            <p>Thank you for using Sqipit!</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return {"subject": subject, "text_body": text_body, "html_body": html_body}


class SMSTemplates:
    @staticmethod
    def queue_subscription(
        customer_name: str, queue_name: str, position: int, estimated_wait: str
    ) -> str:
        return f"Hi {customer_name}! You've joined the queue at {queue_name}. Position: #{position}. Estimated wait: {estimated_wait}. We'll notify you when it's your turn!"

    @staticmethod
    def next_in_line(customer_name: str, queue_name: str, service_location: str) -> str:
        return f"🔔 IT'S YOUR TURN, {customer_name}! Please proceed to {service_location} at {queue_name}. Don't keep them waiting!"

    @staticmethod
    def almost_your_turn(
        customer_name: str, queue_name: str, position: int, estimated_wait: str
    ) -> str:
        return f"⏰ Almost your turn, {customer_name}! Position #{position} at {queue_name}. Est. wait: {estimated_wait}. Please get ready!"

    @staticmethod
    def custom_message(message: str) -> str:
        return message
