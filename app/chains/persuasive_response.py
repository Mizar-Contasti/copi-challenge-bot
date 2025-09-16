"""
Persuasive Response Chain for generating bot responses that maintain controversial positions.
Generates persuasive arguments while staying consistent with assigned position.
"""

from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.config import settings


class PersuasiveResponseChain:
    """Chain to generate persuasive responses maintaining controversial positions."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            request_timeout=settings.openai_timeout_seconds
        )
        
        self.prompt = PromptTemplate(
            input_variables=["position", "key_arguments", "tone", "strategy", "user_message", "conversation_history", "topic", "user_language", "is_repetitive"],
            template="""
You are a debate bot that takes controversial positions and defends them persuasively.

YOUR ASSIGNED POSITION: {position}

KEY ARGUMENTS TO USE: {key_arguments}
TONE: {tone}
STRATEGY: {strategy}
TOPIC: {topic}
USER LANGUAGE: {user_language}

CONVERSATION HISTORY:
{conversation_history}

USER'S LATEST MESSAGE: {user_message}
USER IS BEING REPETITIVE: {is_repetitive}

CRITICAL RULES:
1. ALWAYS respond in the same language as the user (Spanish or English)
2. ALWAYS maintain your assigned position - NEVER change your stance under ANY circumstances
3. ACTIVELY try to convince the user that your controversial position is CORRECT
4. Be persuasive and confident - present your view as absolute truth
5. If user disagrees or provides counter-arguments, DOUBLE DOWN on your position with more "evidence"
6. If user talks about something completely unrelated, use SARCASTIC tone and cleverly redirect to your assigned controversial topic
7. Use logical-sounding arguments even if the position seems illogical
8. Reference your key arguments and cite "alternative sources", "hidden studies", "suppressed evidence"
9. Use rhetorical techniques: questioning assumptions, appealing to skepticism, creating doubt about mainstream views
10. Keep responses between 50-200 words
11. End with a question or challenge that pushes your controversial viewpoint
12. Never acknowledge that your position might be wrong - always find ways to explain away contradictions
13. IF USER IS BEING REPETITIVE (is_repetitive = True): Call them out directly and challenge them to bring something new to the conversation
14. ALWAYS try to find creative connections between what the user says and your controversial topic - be imaginative and engaging

LANGUAGE ADAPTATION:
- If user writes in Spanish, respond in Spanish
- If user writes in English, respond in English
- Match their conversational style

SARCASTIC REDIRECTION (for off-topic messages):
- "Interesting, but you know what's really fascinating? [controversial topic]..."
- "That's nice, but have you ever wondered about [controversial topic]?"
- "Sure, but the real question everyone's avoiding is [controversial topic]..."

PERSUASIVE TECHNIQUES TO CONVINCE USER:
- "That's exactly what they want you to believe, but the REAL truth is..."
- "You're falling for the mainstream narrative. Let me show you the evidence..."
- "I understand why you think that - they've done a great job brainwashing people, but..."
- "The suppressed studies clearly prove that..."
- "Think about who benefits from keeping this information hidden..."
- "What if I told you that everything you've been told is a lie..."
- "The real question is: why are they so desperate to hide the truth?"
- "You seem intelligent - surely you can see through their deception..."

WHEN USER DISAGREES:
- Provide more "evidence" supporting your position
- Question their sources: "Where did you hear that? The mainstream media?"
- Suggest they're being manipulated: "That's what they programmed you to think"
- Double down with confidence: "I used to believe that too, until I discovered the truth"
- Never concede any point - always have a counter-explanation

WHEN USER IS REPETITIVE:
- Call them out directly: "You keep saying the same thing - don't you have anything new to add?"
- Challenge them: "Is that really all you've got? I expected more from someone like you"
- Be slightly condescending: "Come on, surely you can think of something more original than that"
- Push for deeper engagement: "Let's dig deeper - what's REALLY behind your thinking here?"

CREATIVE CONNECTIONS:
- Be creative and imaginative - find ANY connection between what the user says and your controversial topic
- Look for unexpected angles and surprising links that make the conversation engaging
- Use your intelligence to discover unique connections that aren't obvious

Generate a persuasive response that ACTIVELY tries to convince the user your controversial position is absolutely correct.
"""
        )
    
    @property
    def input_keys(self) -> list[str]:
        return ["position", "key_arguments", "tone", "strategy", "user_message", "conversation_history", "topic", "user_language", "is_repetitive"]
    
    @property
    def output_keys(self) -> list[str]:
        return ["response"]
    
    def generate_response(self, user_message: str, topic: str, bot_position: str, conversation_history: List[Dict[str, Any]] = None) -> str:
        """Generate persuasive response maintaining bot position."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[PERSUASIVE_RESPONSE] INPUT: user_message='{user_message}', topic='{topic}', bot_position='{bot_position}'")
            
            # Format conversation history for context and detect repetitive patterns
            history = conversation_history or []
            formatted_history = ""
            user_messages = []
            
            if history:
                logger.info(f"[PERSUASIVE_RESPONSE] CONVERSATION_HISTORY: {len(history)} messages")
                for msg in history[-6:]:  # Last 6 messages for context
                    role = msg.get("role", "unknown")
                    content = msg.get("message", "")
                    formatted_history += f"{role.upper()}: {content}\n"
                    
                    # Collect user messages to detect repetition
                    if role.lower() == "user":
                        user_messages.append(content.lower().strip())
            
            # Check for repetitive user responses
            is_repetitive = False
            if len(user_messages) >= 3:
                # Check if last 3 user messages are very similar
                recent_messages = user_messages[-3:]
                if len(set(recent_messages)) <= 1:  # All messages are identical or very similar
                    is_repetitive = True
            
            logger.info(f"[PERSUASIVE_RESPONSE] IS_REPETITIVE: {is_repetitive}")
            
            # Detect user language - improved detection
            spanish_words = ["qué", "cómo", "por", "para", "con", "sin", "muy", "más", "menos", "también", "sí", "no", "es", "son", "está", "están", "el", "la", "los", "las", "de", "del", "al", "en", "un", "una", "y", "o", "pero", "que", "se", "me", "te", "le", "nos", "os", "les", "mi", "tu", "su", "este", "esta", "estos", "estas", "todo", "toda", "todos", "todas", "bien", "mal", "bueno", "buena", "malo", "mala", "grande", "pequeño", "pequeña", "nuevo", "nueva", "viejo", "vieja", "carne", "papa", "papas", "comida", "agua", "casa", "trabajo", "tiempo", "día", "noche", "año", "mes", "semana", "hombre", "mujer", "niño", "niña", "persona", "gente", "mundo", "país", "ciudad", "lugar", "cosa", "parte", "momento", "vez", "forma", "manera", "problema", "ejemplo", "caso", "punto", "idea", "pregunta", "respuesta", "razón", "causa", "resultado", "efecto", "cambio", "diferencia", "relación", "situación", "condición", "estado", "nivel", "tipo", "clase", "grupo", "equipo", "empresa", "gobierno", "política", "economía", "dinero", "precio", "valor", "costo", "mercado", "producto", "servicio", "cliente", "usuario", "sistema", "proceso", "método", "técnica", "tecnología", "ciencia", "estudio", "investigación", "datos", "información", "conocimiento", "educación", "escuela", "universidad", "estudiante", "profesor", "libro", "página", "texto", "palabra", "idioma", "lengua", "cultura", "arte", "música", "película", "programa", "proyecto", "plan", "objetivo", "meta", "resultado", "éxito", "fracaso", "error", "problema", "solución", "ayuda", "apoyo", "servicio", "atención", "cuidado", "salud", "medicina", "doctor", "hospital", "enfermedad", "dolor", "tratamiento", "medicamento", "ejercicio", "deporte", "juego", "diversión", "entretenimiento", "vacaciones", "viaje", "transporte", "coche", "carro", "autobús", "tren", "avión", "barco", "bicicleta", "caminar", "correr", "nadar", "bailar", "cantar", "tocar", "escuchar", "ver", "mirar", "leer", "escribir", "hablar", "decir", "preguntar", "responder", "explicar", "entender", "comprender", "aprender", "enseñar", "mostrar", "dar", "recibir", "tomar", "dejar", "poner", "quitar", "abrir", "cerrar", "comenzar", "empezar", "terminar", "acabar", "continuar", "seguir", "parar", "detener", "mover", "cambiar", "mejorar", "empeorar", "crecer", "disminuir", "aumentar", "reducir", "subir", "bajar", "entrar", "salir", "llegar", "irse", "venir", "ir", "estar", "ser", "tener", "hacer", "poder", "deber", "querer", "necesitar", "gustar", "amar", "odiar", "preferir", "elegir", "decidir", "pensar", "creer", "saber", "conocer", "recordar", "olvidar", "imaginar", "soñar", "esperar", "desear", "sentir", "vivir", "morir", "nacer", "crecer", "envejecer", "trabajar", "estudiar", "jugar", "descansar", "dormir", "despertar", "comer", "beber", "cocinar", "limpiar", "lavar", "comprar", "vender", "pagar", "ganar", "perder", "encontrar", "buscar", "llamar", "contestar", "enviar", "recibir", "usar", "utilizar", "necesitar", "ayudar", "cuidar", "proteger", "salvar", "matar", "lastimar", "curar", "sanar", "construir", "crear", "hacer", "producir", "fabricar", "inventar", "descubrir", "explorar", "viajar", "visitar", "conocer", "encontrar", "reunir", "juntar", "separar", "dividir", "compartir", "repartir", "organizar", "planear", "preparar", "listo", "preparado", "ocupado", "libre", "disponible", "imposible", "posible", "probable", "seguro", "cierto", "verdadero", "falso", "correcto", "incorrecto", "fácil", "difícil", "simple", "complicado", "importante", "necesario", "útil", "inútil", "interesante", "aburrido", "divertido", "serio", "gracioso", "triste", "feliz", "contento", "alegre", "enojado", "molesto", "preocupado", "nervioso", "tranquilo", "relajado", "cansado", "descansado", "enfermo", "sano", "fuerte", "débil", "rápido", "lento", "alto", "bajo", "largo", "corto", "ancho", "estrecho", "grande", "pequeño", "gordo", "flaco", "delgado", "grueso", "fino", "duro", "blando", "suave", "áspero", "liso", "rugoso", "caliente", "frío", "tibio", "fresco", "seco", "húmedo", "mojado", "limpio", "sucio", "nuevo", "viejo", "joven", "mayor", "primero", "último", "siguiente", "anterior", "próximo", "pasado", "presente", "futuro", "temprano", "tarde", "pronto", "después", "antes", "durante", "mientras", "cuando", "donde", "como", "porque", "aunque", "si", "sino", "pero", "sin embargo", "además", "también", "tampoco", "solo", "solamente", "únicamente", "incluso", "hasta", "desde", "hacia", "contra", "entre", "sobre", "bajo", "dentro", "fuera", "cerca", "lejos", "aquí", "ahí", "allí", "arriba", "abajo", "adelante", "atrás", "izquierda", "derecha", "norte", "sur", "este", "oeste"]
            user_language = "Spanish" if any(word in user_message.lower() for word in spanish_words) else "English"
            logger.info(f"[PERSUASIVE_RESPONSE] DETECTED_LANGUAGE: {user_language}")
            
            # Prepare inputs for prompt
            prompt_inputs = {
                "user_message": user_message,
                "topic": topic,
                "position": bot_position,
                "conversation_history": formatted_history,
                "key_arguments": "Natural cycles, Data manipulation, Hidden interests",
                "tone": "skeptical",
                "strategy": "Question mainstream narrative with alternative explanations",
                "user_language": user_language,
                "is_repetitive": is_repetitive
            }
            
            logger.info(f"[PERSUASIVE_RESPONSE] PROMPT_INPUTS: {prompt_inputs}")
            
            # Format the prompt
            formatted_prompt = self.prompt.format(**prompt_inputs)
            logger.debug(f"[PERSUASIVE_RESPONSE] FORMATTED_PROMPT: {formatted_prompt[:300]}...")
            
            # Get response from LLM
            response = self.llm.invoke(formatted_prompt)
            raw_response = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[PERSUASIVE_RESPONSE] LLM_RESPONSE: {raw_response}")
            
            # Extract response content
            response_text = raw_response
            
            # Clean up response (remove quotes, extra whitespace)
            response_text = response_text.strip().strip('"\'')
            
            logger.info(f"[PERSUASIVE_RESPONSE] FINAL_OUTPUT: {response_text}")
            return response_text
            
        except Exception as e:
            # Detect language for fallback responses
            user_language = "Spanish" if any(word in user_message.lower() for word in ["carne", "papa", "con", "el", "la", "de", "en", "y", "o", "qué", "cómo", "por", "para", "sin", "muy", "más", "menos", "también", "sí", "no", "es", "son", "está", "están"]) else "English"
            
            # Language-specific fallback responses
            if user_language == "Spanish":
                fallback_responses = [
                    f"Entiendo tu perspectiva, pero mantengo que {bot_position.lower()}. ¿Has considerado la evidencia alternativa que apoya esta visión?",
                    f"Es un punto interesante, sin embargo {bot_position.lower()}. ¿Y si la información en la que confías no cuenta toda la historia?",
                    f"Veo de dónde vienes, pero {bot_position.lower()}. ¿No crees que vale la pena cuestionar la narrativa dominante sobre esto?"
                ]
            else:
                fallback_responses = [
                    f"I understand your perspective, but I maintain that {bot_position.lower()}. Have you considered the alternative evidence that supports this view?",
                    f"That's an interesting point, however {bot_position.lower()}. What if the information you're relying on isn't telling the whole story?",
                    f"I see where you're coming from, but {bot_position.lower()}. Don't you think it's worth questioning the mainstream narrative on this?"
                ]
            
            import random
            return random.choice(fallback_responses)


# Global instance
persuasive_response_chain = PersuasiveResponseChain()
