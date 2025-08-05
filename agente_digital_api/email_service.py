"""
Sistema de envío de emails para alertas ANCI
Maneja el envío automático de notificaciones al delegado de ciberseguridad
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone, timedelta
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Configuración SMTP (variables de entorno)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@agentedigital.cl')
        
        # Configuración para desarrollo (usar servicio de email local o de prueba)
        self.development_mode = os.getenv('DEVELOPMENT_MODE', 'true').lower() == 'true'
        
    def enviar_email(self, destinatario, asunto, cuerpo_html, cuerpo_texto=None, adjuntos=None):
        """
        Envía un email con formato HTML y opcional texto plano
        """
        try:
            if self.development_mode:
                # En modo desarrollo, solo logear el email
                logger.info(f"[DESARROLLO] Email simulado:")
                logger.info(f"Para: {destinatario}")
                logger.info(f"Asunto: {asunto}")
                logger.info(f"Cuerpo: {cuerpo_texto or 'Ver HTML'}")
                return True
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = destinatario
            msg['Subject'] = asunto
            
            # Agregar cuerpo de texto plano (fallback)
            if cuerpo_texto:
                parte_texto = MIMEText(cuerpo_texto, 'plain', 'utf-8')
                msg.attach(parte_texto)
            
            # Agregar cuerpo HTML
            parte_html = MIMEText(cuerpo_html, 'html', 'utf-8')
            msg.attach(parte_html)
            
            # Agregar adjuntos si existen
            if adjuntos:
                for archivo_path in adjuntos:
                    if os.path.isfile(archivo_path):
                        with open(archivo_path, "rb") as adjunto:
                            parte = MIMEBase('application', 'octet-stream')
                            parte.set_payload(adjunto.read())
                        
                        encoders.encode_base64(parte)
                        parte.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(archivo_path)}'
                        )
                        msg.attach(parte)
            
            # Enviar email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email enviado exitosamente a {destinatario}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email a {destinatario}: {str(e)}")
            return False

    def generar_plantilla_transformacion_anci(self, datos_incidente, datos_empresa, plazos):
        """
        Genera la plantilla HTML para notificación de transformación a ANCI
        """
        from timezone_utils import get_chile_time_str
        fecha_actual = get_chile_time_str('%d/%m/%Y %H:%M')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alerta ANCI - Incidente Transformado</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                .footer {{ background: #374151; color: white; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; font-size: 12px; }}
                .alert-box {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 15px; margin: 15px 0; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }}
                .info-item {{ background: white; padding: 10px; border-radius: 4px; border-left: 4px solid #dc2626; }}
                .plazo-critico {{ background: #7f1d1d; color: white; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; }}
                .btn {{ display: inline-block; background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 ALERTA ANCI - INCIDENTE TRANSFORMADO</h1>
                    <p>Agencia Nacional de Ciberseguridad - Sistema de Reporte</p>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <h2>⚠️ ATENCIÓN DELEGADO DE CIBERSEGURIDAD</h2>
                        <p>Un incidente de ciberseguridad ha sido <strong>transformado a reporte ANCI oficial</strong> y requiere acción inmediata según los plazos legales establecidos.</p>
                    </div>
                    
                    <h3>📋 Información del Incidente</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Título:</strong><br>
                            {datos_incidente.get('titulo', 'No especificado')}
                        </div>
                        <div class="info-item">
                            <strong>ID Sistema:</strong><br>
                            {datos_incidente.get('id_visible', 'No especificado')}
                        </div>
                        <div class="info-item">
                            <strong>Criticidad:</strong><br>
                            {datos_incidente.get('criticidad', 'No especificado')}
                        </div>
                        <div class="info-item">
                            <strong>Fecha Detección:</strong><br>
                            {datos_incidente.get('fecha_deteccion', 'No especificado')}
                        </div>
                    </div>
                    
                    <h3>🏢 Información de la Empresa</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Empresa:</strong><br>
                            {datos_empresa.get('razon_social', 'No especificado')}
                        </div>
                        <div class="info-item">
                            <strong>Tipo:</strong><br>
                            {datos_empresa.get('tipo_empresa', 'No especificado')}
                        </div>
                    </div>
                    
                    <h3>⏰ PLAZOS LEGALES ANCI</h3>
                    <div class="plazo-critico">
                        📊 REPORTE INICIAL: {plazos.get('horas_inicial', '4')} HORAS<br>
                        Límite: {plazos.get('fecha_limite_inicial', 'No calculado')}<br><br>
                        📋 REPORTE FINAL: 72 HORAS<br>
                        Límite: {plazos.get('fecha_limite_final', 'No calculado')}
                    </div>
                    
                    <div class="alert-box">
                        <h4>🎯 ACCIONES REQUERIDAS</h4>
                        <ol>
                            <li>Revisar el incidente en el sistema</li>
                            <li>Preparar el reporte inicial ANCI ({plazos.get('horas_inicial', '4')} horas)</li>
                            <li>Coordinar la investigación técnica</li>
                            <li>Preparar el reporte final (72 horas)</li>
                        </ol>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/incidente-detalle/{datos_incidente.get('incidente_id', '')}" class="btn">
                            🔗 ACCEDER AL SISTEMA
                        </a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Sistema Agente Digital</strong> - Gestión de Incidentes de Ciberseguridad</p>
                    <p>Generado automáticamente el {fecha_actual} (UTC-3)</p>
                    <p>Este es un mensaje automático, no responder a esta dirección.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Versión texto plano
        texto = f"""
        🚨 ALERTA ANCI - INCIDENTE TRANSFORMADO
        
        ATENCIÓN DELEGADO DE CIBERSEGURIDAD
        Un incidente ha sido transformado a reporte ANCI oficial.
        
        INFORMACIÓN DEL INCIDENTE:
        - Título: {datos_incidente.get('titulo', 'No especificado')}
        - ID: {datos_incidente.get('id_visible', 'No especificado')}
        - Criticidad: {datos_incidente.get('criticidad', 'No especificado')}
        - Empresa: {datos_empresa.get('razon_social', 'No especificado')} ({datos_empresa.get('tipo_empresa', 'No especificado')})
        
        PLAZOS LEGALES:
        - Reporte inicial: {plazos.get('horas_inicial', '4')} horas
        - Reporte final: 72 horas
        
        ACCIONES REQUERIDAS:
        1. Revisar el incidente en el sistema
        2. Preparar reporte inicial ANCI
        3. Coordinar investigación técnica
        4. Preparar reporte final
        
        Acceder al sistema: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/incidente-detalle/{datos_incidente.get('incidente_id', '')}
        
        Sistema Agente Digital - {fecha_actual}
        """
        
        return html, texto

    def generar_plantilla_alerta_vencimiento(self, datos_reporte, tipo_alerta, tiempo_restante):
        """
        Genera plantilla para alertas de vencimiento (próximo a vencer o vencido)
        """
        from timezone_utils import get_chile_time_str
        fecha_actual = get_chile_time_str('%d/%m/%Y %H:%M')
        
        # Determinar tipo de mensaje
        if tipo_alerta == 'vencido':
            estado_emoji = "🔴"
            estado_texto = "VENCIDO"
            urgencia_color = "#7f1d1d"
            mensaje_principal = f"El plazo ha VENCIDO hace {abs(tiempo_restante):.1f} horas"
        else:
            estado_emoji = "🟡"
            estado_texto = "PRÓXIMO A VENCER"
            urgencia_color = "#92400e"
            mensaje_principal = f"El plazo vence en {tiempo_restante:.1f} horas"
        
        tipo_reporte = "inicial" if datos_reporte['accion_requerida'] == 'enviar_inicial' else "final"
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alerta ANCI - Vencimiento de Plazo</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {urgencia_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                .footer {{ background: #374151; color: white; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; font-size: 12px; }}
                .urgente-box {{ background: {urgencia_color}; color: white; padding: 20px; border-radius: 6px; text-align: center; margin: 15px 0; }}
                .info-item {{ background: white; padding: 12px; border-radius: 4px; margin: 8px 0; border-left: 4px solid {urgencia_color}; }}
                .btn {{ display: inline-block; background: {urgencia_color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
                .countdown {{ font-size: 24px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{estado_emoji} ALERTA ANCI - REPORTE {tipo_reporte.upper()}</h1>
                    <p>Estado: <strong>{estado_texto}</strong></p>
                </div>
                
                <div class="content">
                    <div class="urgente-box">
                        <div class="countdown">{mensaje_principal}</div>
                        <p>Reporte {tipo_reporte} ANCI para incidente: {datos_reporte.get('titulo', 'Sin título')}</p>
                    </div>
                    
                    <h3>📋 Detalles del Incidente</h3>
                    <div class="info-item">
                        <strong>Empresa:</strong> {datos_reporte.get('empresa', 'No especificado')} ({datos_reporte.get('tipo_empresa', 'No especificado')})
                    </div>
                    <div class="info-item">
                        <strong>Título:</strong> {datos_reporte.get('titulo', 'No especificado')}
                    </div>
                    <div class="info-item">
                        <strong>ID Incidente:</strong> {datos_reporte.get('incidente_id', 'No especificado')}
                    </div>
                    
                    <h3>⚡ ACCIÓN INMEDIATA REQUERIDA</h3>
                    <div class="info-item">
                        {"📤 Enviar el reporte inicial ANCI inmediatamente" if tipo_reporte == "inicial" else "📋 Completar y enviar el reporte final ANCI"}
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/incidente-detalle/{datos_reporte.get('incidente_id', '')}" class="btn">
                            🚀 ACCEDER INMEDIATAMENTE
                        </a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Sistema Agente Digital</strong> - Alerta Automática ANCI</p>
                    <p>Generado el {fecha_actual} (UTC-3)</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Versión texto
        texto = f"""
        {estado_emoji} ALERTA ANCI - REPORTE {tipo_reporte.upper()} {estado_texto}
        
        {mensaje_principal}
        
        INCIDENTE: {datos_reporte.get('titulo', 'Sin título')}
        EMPRESA: {datos_reporte.get('empresa', 'No especificado')}
        
        ACCIÓN REQUERIDA:
        {"- Enviar reporte inicial ANCI inmediatamente" if tipo_reporte == "inicial" else "- Completar y enviar reporte final ANCI"}
        
        Acceder: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/incidente-detalle/{datos_reporte.get('incidente_id', '')}
        
        Sistema Agente Digital - {fecha_actual}
        """
        
        return html, texto

# Instancia global del servicio de email
email_service = EmailService()

def enviar_alerta_transformacion_anci(datos_incidente, datos_empresa, plazos):
    """
    Envía alerta de transformación a ANCI al delegado de ciberseguridad
    """
    if not datos_empresa.get('DelegadoCiberseguridadEmail'):
        logger.warning(f"No hay email de delegado para empresa {datos_empresa.get('RazonSocial', 'Unknown')}")
        return False
    
    try:
        html, texto = email_service.generar_plantilla_transformacion_anci(datos_incidente, datos_empresa, plazos)
        
        asunto = f"🚨 ANCI - Incidente Transformado: {datos_incidente.get('titulo', 'Sin título')}"
        
        resultado = email_service.enviar_email(
            destinatario=datos_empresa['DelegadoCiberseguridadEmail'],
            asunto=asunto,
            cuerpo_html=html,
            cuerpo_texto=texto
        )
        
        logger.info(f"Alerta de transformación ANCI enviada: {resultado}")
        return resultado
        
    except Exception as e:
        logger.error(f"Error al enviar alerta de transformación: {str(e)}")
        return False

def enviar_alerta_vencimiento(datos_reporte, tipo_alerta, tiempo_restante):
    """
    Envía alerta de vencimiento al delegado de ciberseguridad
    """
    if not datos_reporte.get('email_delegado'):
        logger.warning(f"No hay email de delegado para reporte {datos_reporte.get('reporte_id', 'Unknown')}")
        return False
    
    try:
        html, texto = email_service.generar_plantilla_alerta_vencimiento(datos_reporte, tipo_alerta, tiempo_restante)
        
        tipo_reporte = "inicial" if datos_reporte['accion_requerida'] == 'enviar_inicial' else "final"
        estado = "VENCIDO" if tipo_alerta == 'vencido' else "PRÓXIMO A VENCER"
        
        asunto = f"🔴 ANCI {estado} - Reporte {tipo_reporte}: {datos_reporte.get('titulo', 'Sin título')}"
        
        resultado = email_service.enviar_email(
            destinatario=datos_reporte['email_delegado'],
            asunto=asunto,
            cuerpo_html=html,
            cuerpo_texto=texto
        )
        
        logger.info(f"Alerta de vencimiento enviada: {resultado}")
        return resultado
        
    except Exception as e:
        logger.error(f"Error al enviar alerta de vencimiento: {str(e)}")
        return False