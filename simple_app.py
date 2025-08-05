from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <html>
        <head>
            <title>Agente Digital</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #333; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <h1>¡Agente Digital está funcionando!</h1>
            <p>La aplicación se desplegó correctamente en Railway</p>
            <p>Versión: Test Simple</p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "ok", "message": "Servidor funcionando", "port": os.environ.get('PORT', 'No definido')}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)