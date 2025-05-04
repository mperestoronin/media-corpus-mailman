from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import os

app = Flask(__name__)

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

def create_digest_html(title, web_link, text=None, pdf=False):
    content = "Содержимое дайджеста во вложении." if pdf else text
    html = f"""
    <html>
      <body style="background-color: #ffffff; color: #333333; font-family: Arial, sans-serif; padding: 20px;">
        <!-- Логотип компании -->
        <div style="text-align: center; margin-bottom: 20px;">
          <img src="https://cdn.emailacademy.com/user/unregistered/crosswords_logo2025_03_31_15_39_32.png" alt="Логотип компании" style="max-width:200px;">
        </div>
        <!-- Название письма -->
        <h1 style="text-align: center;"><b>{title}</b></h1>
        <!-- Основное содержимое -->
        <p>{content}</p>
        <!-- Кнопка с ссылкой на веб-версию -->
        <div style="text-align: center; margin-top: 30px;">
          <a href="{web_link}" style="display: inline-block; padding: 10px 20px; background-color: #ffdd2d; color: #333333; text-decoration: none; border-radius: 5px;">
            Открыть в корпусе
          </a>
        </div>
      </body>
    </html>
    """
    return html

@app.route('/send-email', methods=['POST'])
def send_email():
    if request.is_json:
        data = request.get_json()
        recipients = data.get('recipients')
        title = data.get('title')
        text = data.get('text')
        web_link = data.get('web_link')
        pdf_file = None
    else:
        recipients = request.form.getlist('recipients')
        title = request.form.get('title')
        text = request.form.get('text')
        web_link = request.form.get('web_link')
        pdf_file = request.files.get('pdf')

    if not recipients or not title or not web_link:
        return jsonify(
            {"error": "Отсутствуют необходимые параметры: recipients, title или web_link"}), 400
    pdf_present = pdf_file is not None

    if not pdf_present and not text:
        return jsonify({"error": "Не передан ни текст, ни PDF файл. Должен быть передан один из параметров."}), 400

    subject = f"Ежедневный дайджест - {title}"
    html_body = create_digest_html(title, web_link, text=text, pdf=pdf_present)

    try:
        msg = Message(subject, recipients=recipients, html=html_body)

        if pdf_present:
            pdf_data = pdf_file.read()
            msg.attach(pdf_file.filename, 'application/pdf', pdf_data)
        mail.send(msg)
        return jsonify({"message": "Email отправлен успешно"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_verification_html(code):
    html = f"""
    <html>
      <body style="background-color: #ffffff; color: #333333; font-family: Arial, sans-serif; padding: 20px;">
        <!-- Логотип компании -->
        <div style="text-align: center; margin-bottom: 20px;">
          <img src="https://cdn.emailacademy.com/user/unregistered/crosswords_logo2025_03_31_15_39_32.png" alt="Логотип компании" style="max-width:200px;">
        </div>

        <p style="font-size: 18px;">Введите данный код регистрации на нашем сайте, чтобы завершить регистрацию.</p>

        <p style="text-align: center; font-size: 32px; font-weight: bold; margin: 20px 0;">{code}</p>

        <p>Спасибо, что выбрали Crosswords! 🎉</p>
        <p>Теперь вы в курсе всего важного: свежие новости, эксклюзивные материалы и только самое интересное — без лишнего шума.</p>
        <p>Надеемся, вам у нас понравится! Если нужна помощь или есть пожелания — просто напишите.</p>
        <p>Всегда на связи.</p>
        <p>Приятного чтения! 😊</p>
      </body>
    </html>
    """
    return html


@app.route('/verify_email', methods=['POST'])
def verify_email():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        return jsonify({"error": "Поля 'email' и 'code' обязательны"}), 400

    try:
        html_body = create_verification_html(code)
        msg = Message("Код подтверждения регистрации", recipients=[email], html=html_body)
        mail.send(msg)
        return jsonify({"message": "Письмо с кодом отправлено"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False)
