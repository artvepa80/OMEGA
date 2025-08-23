#!/usr/bin/env python3
"""
🇵🇪 Peru Responsible Gaming Resources
Comprehensive Peru-specific resources for responsible gaming and legal compliance
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class PeruHelpResource:
    """Peru-specific help resource"""
    name: str
    description: str
    phone: Optional[str]
    website: Optional[str] 
    address: Optional[str]
    email: Optional[str]
    service_type: str
    availability: str
    cost: str
    language: str

class PeruResponsibleGamingResources:
    """Comprehensive Peru responsible gaming resources"""
    
    def __init__(self):
        self.emergency_line = "113"
        self.country_code = "+51"
        self.resources = self._load_peru_resources()
    
    def _load_peru_resources(self) -> Dict[str, List[PeruHelpResource]]:
        """Load comprehensive Peru-specific help resources"""
        
        return {
            "government_agencies": [
                PeruHelpResource(
                    name="Ministerio de Justicia y Derechos Humanos (MINJUS)",
                    description="Línea nacional gratuita para problemas de adicciones",
                    phone="113",
                    website="https://www.gob.pe/minjus",
                    address="Av. Scipión Llona 350, Miraflores, Lima",
                    email="consultas@minjus.gob.pe",
                    service_type="Línea de ayuda gubernamental",
                    availability="24 horas, 7 días",
                    cost="Gratuito",
                    language="Español"
                ),
                PeruHelpResource(
                    name="Ministerio de Salud (MINSA)",
                    description="Información sobre ludopatía como enfermedad reconocida",
                    phone="(01) 315-6600",
                    website="https://www.gob.pe/minsa",
                    address="Av. Salaverry 801, Jesús María, Lima", 
                    email="webmaster@minsa.gob.pe",
                    service_type="Política de salud pública",
                    availability="Horario de oficina",
                    cost="Gratuito",
                    language="Español"
                )
            ],
            
            "addiction_treatment": [
                PeruHelpResource(
                    name="CEDRO - Centro de Información y Educación para la Prevención del Abuso de Drogas",
                    description="Tratamiento especializado en adicciones incluyendo ludopatía",
                    phone="(01) 445-6665",
                    website="https://www.cedro.org.pe",
                    address="Av. Roca y Boloña 271, San Antonio, Miraflores",
                    email="postmaster@cedro.org.pe",
                    service_type="Centro especializado en adicciones",
                    availability="Lunes a viernes 8:30-17:30",
                    cost="Consulta inicial gratuita, tratamientos con costo",
                    language="Español"
                ),
                PeruHelpResource(
                    name="Instituto Nacional de Salud Mental 'Honorio Delgado-Hideyo Noguchi'",
                    description="Atención psiquiátrica y psicológica especializada",
                    phone="(01) 613-4800",
                    website="https://www.insm.gob.pe",
                    address="Av. Honorio Delgado 262, San Martín de Porres, Lima",
                    email="instituto@insm.gob.pe", 
                    service_type="Instituto nacional de salud mental",
                    availability="24 horas emergencias, consultas programadas",
                    cost="Seguro integral de salud (SIS)",
                    language="Español"
                ),
                PeruHelpResource(
                    name="Hospital Nacional Dos de Mayo",
                    description="Servicio de psiquiatría con programa de adicciones",
                    phone="(01) 328-0028",
                    website="https://www.dos-de-mayo.gob.pe",
                    address="Av. Grau cuadra 13, Cercado de Lima",
                    email="mesa.partes@dos-de-mayo.gob.pe",
                    service_type="Hospital público con especialidad",
                    availability="Emergencias 24h, consultas programadas",
                    cost="SIS y seguros públicos",
                    language="Español"
                )
            ],
            
            "support_groups": [
                PeruHelpResource(
                    name="Jugadores Anónimos Lima",
                    description="Grupos de apoyo gratuitos basados en 12 pasos",
                    phone="999-123-456",  # Placeholder - grupos suelen tener varios contactos
                    website="https://www.jugadoresanonimos.org",
                    address="Varias ubicaciones en Lima",
                    email="lima@jugadoresanonimos.pe",
                    service_type="Grupos de autoayuda",
                    availability="Reuniones semanales",
                    cost="Gratuito (contribuciones voluntarias)",
                    language="Español"
                ),
                PeruHelpResource(
                    name="Narcóticos Anónimos Perú",
                    description="Programa de recuperación que incluye adicciones conductuales",
                    phone="(01) 981-417-085",
                    website="https://www.na-peru.org",
                    address="Múltiples ubicaciones en Lima y provincias",
                    email="webservant@na-peru.org",
                    service_type="Programa de 12 pasos",
                    availability="Reuniones diarias en diferentes horarios",
                    cost="Gratuito",
                    language="Español"
                )
            ],
            
            "private_clinics": [
                PeruHelpResource(
                    name="Centro Takiwasi",
                    description="Centro especializado en adicciones con enfoque integral",
                    phone="(042) 522-818",
                    website="https://www.takiwasi.com",
                    address="Prolongación Alerta 466, Tarapoto, San Martín",
                    email="contact@takiwasi.com",
                    service_type="Centro privado especializado",
                    availability="Programas residenciales",
                    cost="Privado con planes de financiamiento",
                    language="Español, Inglés, Francés"
                ),
                PeruHelpResource(
                    name="Clínica Alemana Lima",
                    description="Servicio de psiquiatría y psicología clínica",
                    phone="(01) 712-3000",
                    website="https://www.alemana.pe",
                    address="Av. Arequipa 1148, Lima",
                    email="informes@alemana.pe",
                    service_type="Clínica privada",
                    availability="Consultas programadas",
                    cost="Privado, acepta seguros",
                    language="Español, Alemán"
                )
            ],
            
            "legal_aid": [
                PeruHelpResource(
                    name="Defensoría del Pueblo",
                    description="Protección de derechos del consumidor y acceso a salud",
                    phone="(01) 311-0300",
                    website="https://www.defensoria.gob.pe",
                    address="Jr. Ucayali 388, Lima",
                    email="defensor@defensoria.gob.pe",
                    service_type="Institución estatal de derechos",
                    availability="Horario de oficina",
                    cost="Gratuito",
                    language="Español, idiomas nativos"
                ),
                PeruHelpResource(
                    name="INDECOPI - Protección al Consumidor",
                    description="Denuncias sobre publicidad engañosa en juegos de azar",
                    phone="(01) 224-7777",
                    website="https://www.indecopi.gob.pe",
                    address="Calle De La Prosa 104, Lima",
                    email="postmaster@indecopi.gob.pe", 
                    service_type="Protección al consumidor",
                    availability="Horario de oficina",
                    cost="Gratuito para consumidores",
                    language="Español"
                )
            ],
            
            "online_resources": [
                PeruHelpResource(
                    name="Portal de Salud Mental MINSA",
                    description="Información y recursos sobre salud mental",
                    phone=None,
                    website="https://www.saludmental.gob.pe",
                    address=None,
                    email="saludmental@minsa.gob.pe",
                    service_type="Portal informativo",
                    availability="24/7 en línea",
                    cost="Gratuito",
                    language="Español"
                ),
                PeruHelpResource(
                    name="Chat de Ayuda Psicológica - Universidad Cayetano Heredia",
                    description="Chat gratuito de apoyo psicológico",
                    phone=None,
                    website="https://www.upch.edu.pe/chat-psicologico",
                    address=None,
                    email="psicologia@upch.edu.pe",
                    service_type="Chat de apoyo online",
                    availability="Horarios específicos",
                    cost="Gratuito",
                    language="Español"
                )
            ]
        }
    
    def get_emergency_contact(self, locale: str = "es") -> Dict[str, str]:
        """Get emergency contact information"""
        
        if locale == "es":
            return {
                "title": "🆘 EMERGENCIA LUDOPATÍA PERÚ",
                "primary_line": "113",
                "description": "Línea gratuita MINJUS - disponible 24 horas",
                "backup_line": "(01) 445-6665",
                "backup_description": "CEDRO - Centro especializado en adicciones",
                "instruction": "Si tienes pensamientos de autolesión, llama inmediatamente a emergencias 105 o acude al hospital más cercano."
            }
        else:
            return {
                "title": "🆘 PERU GAMBLING ADDICTION EMERGENCY",
                "primary_line": "113", 
                "description": "Free MINJUS line - available 24 hours",
                "backup_line": "(01) 445-6665",
                "backup_description": "CEDRO - Specialized addiction center",
                "instruction": "If you have thoughts of self-harm, immediately call emergency 105 or go to the nearest hospital."
            }
    
    def get_resources_by_category(self, category: str) -> List[PeruHelpResource]:
        """Get resources by category"""
        return self.resources.get(category, [])
    
    def get_all_phone_numbers(self) -> List[str]:
        """Get all available phone numbers for quick reference"""
        phones = ["113"]  # Emergency line first
        
        for category in self.resources.values():
            for resource in category:
                if resource.phone:
                    phones.append(resource.phone)
        
        return phones
    
    def format_resource_for_message(self, resource: PeruHelpResource, locale: str = "es") -> str:
        """Format resource information for messaging"""
        
        if locale == "es":
            formatted = f"**{resource.name}**\n"
            formatted += f"📋 {resource.description}\n"
            
            if resource.phone:
                formatted += f"📞 {resource.phone}\n"
            if resource.website:
                formatted += f"🌐 {resource.website}\n"
            if resource.address:
                formatted += f"📍 {resource.address}\n"
            if resource.email:
                formatted += f"📧 {resource.email}\n"
            
            formatted += f"⏰ {resource.availability}\n"
            formatted += f"💰 {resource.cost}"
            
        else:
            formatted = f"**{resource.name}**\n"
            formatted += f"📋 {resource.description}\n"
            
            if resource.phone:
                formatted += f"📞 {resource.phone}\n"
            if resource.website:
                formatted += f"🌐 {resource.website}\n"
            if resource.address:
                formatted += f"📍 {resource.address}\n"
            if resource.email:
                formatted += f"📧 {resource.email}\n"
            
            formatted += f"⏰ {resource.availability}\n"
            formatted += f"💰 {resource.cost}"
        
        return formatted
    
    def get_comprehensive_help_message(self, trigger_level: str = "general", locale: str = "es") -> str:
        """Get comprehensive help message based on trigger level"""
        
        if locale == "es":
            if trigger_level == "critical":
                message = """🚨 **AYUDA INMEDIATA - PERÚ**

**EMERGENCIA**: Si tienes pensamientos de autolesión, llama 105 o acude al hospital más cercano.

**LUDOPATÍA - LÍNEA GRATUITA**:
📞 113 (MINJUS) - Disponible 24 horas

**CENTROS ESPECIALIZADOS**:
🏥 CEDRO: (01) 445-6665
🏥 Instituto Nacional de Salud Mental: (01) 613-4800

**GRUPOS DE APOYO GRATUITOS**:
👥 Jugadores Anónimos Lima
👥 Narcóticos Anónimos Perú

⚖️ **IMPORTANTE**: En Perú, la ludopatía es reconocida oficialmente como enfermedad por el MINSA. Tienes derecho a tratamiento.

💡 **PRÓXIMO PASO**: Llama al 113 ahora mismo. La llamada es gratuita y confidencial."""

            elif trigger_level == "moderate":
                message = """🎗️ **RECURSOS DE AYUDA - PERÚ**

¿Te preocupa tu relación con los juegos de azar? No estás solo.

**EVALUACIÓN GRATUITA**:
📞 113 (MINJUS) - Línea gratuita
📞 (01) 445-6665 (CEDRO)

**SEÑALES DE ALERTA**:
• Apostar más de lo planeado
• Sentir ansiedad cuando no puedes jugar
• Mentir sobre tus actividades de juego
• Usar el juego para escapar de problemas

**APOYO DISPONIBLE**:
🏥 Tratamiento profesional (SIS acepto en hospitales públicos)
👥 Grupos de apoyo gratuitos
💻 Recursos en línea

La ayuda está disponible y funciona. Muchas personas se han recuperado."""

            else:  # general
                message = """🛡️ **JUEGO RESPONSABLE - PERÚ**

**RECUERDA**:
• Los juegos son entretenimiento, no inversión
• Nunca juegues dinero que necesitas para gastos esenciales
• La "suerte" no existe - todos los sorteos son aleatorios
• Las pérdidas no se "recuperan" con más juego

**SI NECESITAS AYUDA**:
📞 113 - Línea gratuita MINJUS
🌐 www.cedro.org.pe - Centro especializado

⚖️ **LEGAL**: OMEGA cumple con regulaciones peruanas. Solo proporcionamos análisis estadístico educativo para mayores de 18 años."""

        else:  # English
            if trigger_level == "critical":
                message = """🚨 **IMMEDIATE HELP - PERU**

**EMERGENCY**: If you have thoughts of self-harm, call 105 or go to the nearest hospital.

**GAMBLING ADDICTION - FREE LINE**:
📞 113 (MINJUS) - Available 24 hours

**SPECIALIZED CENTERS**:
🏥 CEDRO: (01) 445-6665
🏥 National Institute of Mental Health: (01) 613-4800

**FREE SUPPORT GROUPS**:
👥 Gamblers Anonymous Lima
👥 Narcotics Anonymous Peru

⚖️ **IMPORTANT**: In Peru, gambling addiction is officially recognized as a disease by MINSA. You have the right to treatment.

💡 **NEXT STEP**: Call 113 right now. The call is free and confidential."""

            else:
                message = """🛡️ **RESPONSIBLE GAMING - PERU**

**REMEMBER**:
• Games are entertainment, not investment
• Never gamble money you need for essential expenses
• "Luck" doesn't exist - all drawings are random
• Losses are not "recovered" with more gambling

**IF YOU NEED HELP**:
📞 113 - MINJUS free line
🌐 www.cedro.org.pe - Specialized center

⚖️ **LEGAL**: OMEGA complies with Peruvian regulations. We only provide educational statistical analysis for adults over 18."""
        
        return message
    
    def get_prevention_tips(self, locale: str = "es") -> List[str]:
        """Get gambling addiction prevention tips"""
        
        if locale == "es":
            return [
                "Establece un límite de dinero antes de jugar y respétalo siempre",
                "Nunca juegues cuando estés molesto, estresado o deprimido",
                "No uses tarjetas de crédito para jugar",
                "Limita el tiempo que dedicas a juegos de azar",
                "Busca actividades alternativas de entretenimiento",
                "Habla con familiares y amigos sobre tus hábitos de juego",
                "Considera usar herramientas de autoexclusión",
                "Recuerda que la casa siempre tiene ventaja matemática",
                "No veas el juego como una forma de hacer dinero",
                "Si pierdes, acepta la pérdida y no trates de 'recuperar'"
            ]
        else:
            return [
                "Set a money limit before playing and always respect it",
                "Never gamble when upset, stressed, or depressed", 
                "Don't use credit cards to gamble",
                "Limit the time you spend on gambling",
                "Seek alternative entertainment activities",
                "Talk to family and friends about your gambling habits",
                "Consider using self-exclusion tools",
                "Remember the house always has mathematical advantage",
                "Don't view gambling as a way to make money",
                "If you lose, accept the loss and don't try to 'recover'"
            ]
    
    def generate_weekly_reminder(self, locale: str = "es") -> str:
        """Generate weekly responsible gaming reminder"""
        
        week_num = datetime.now().isocalendar()[1]
        tip_index = week_num % len(self.get_prevention_tips(locale))
        
        tip = self.get_prevention_tips(locale)[tip_index]
        
        if locale == "es":
            return f"""📅 **Recordatorio Semanal de Juego Responsable**

💡 **Tip de la Semana**: {tip}

🆘 **Recuerda**: Si necesitas ayuda, llama al 113 (gratuito)
⚖️ **Legal**: OMEGA es una herramienta educativa, no garantiza ganancias.

Juega responsablemente. 🎯"""
        else:
            return f"""📅 **Weekly Responsible Gaming Reminder**

💡 **Tip of the Week**: {tip}

🆘 **Remember**: If you need help, call 113 (free)
⚖️ **Legal**: OMEGA is an educational tool, doesn't guarantee wins.

Play responsibly. 🎯"""


# Global instance for easy access
peru_resources = PeruResponsibleGamingResources()