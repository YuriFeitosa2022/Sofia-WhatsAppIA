# Sofia - Agente de IA para WhatsApp 🤖

## 📝 Descrição do Projeto

Sofia é uma agente de IA conversacional projetado para interagir com usuários/clientes através do WhatsApp. O projeto foi construído e focado como uma solução para automatizar e otimizar o atendimento na área de assistência técnica, servindo como um protótipo funcional e robusto.

A aplicação utiliza um servidor web **Flask** como webhook para a API do **Twilio**, que gerencia a comunicação com o WhatsApp. O cérebro da Sofia é alimentado pela API do **Google Gemini**, permitindo um processamento de linguagem natural avançado para conversas fluidas e contextuais.

## ✨ Funcionalidades Principais

-   **Servidor Web com Flask:** Estrutura de backend leve e eficiente para receber e responder às mensagens do WhatsApp em tempo real.
-   **Processamento Assíncrono:** Utiliza `threading` para processar requisições complexas em segundo plano, garantindo que o webhook responda rapidamente ao Twilio e evite timeouts.
-   **Skill de Negócio (Consulta de Garantia):** A Sofia possui uma "skill" específica para consultar o status de garantia de produtos. Ela lê e interpreta dados de um arquivo `.csv` utilizando a biblioteca **Pandas**, demonstrando capacidade de integração com bases de dados locais.
-   **Gerenciamento de Contexto:** Um sistema simples de "memória de curto prazo" permite que a Sofia realize conversas de múltiplos passos (ex: pedir um número de Ordem de Produção e depois agir com base nesse número).
-   **Notificação Ativa:** Capacidade de enviar alertas resumidos para um número predefinido em caso de eventos específicos, como a necessidade de intervenção humana ("transbordo").

## 🚀 Tecnologias Utilizadas

-   **Linguagem:** Python
-   **Servidor Web:** Flask
-   **IA / LLM:** Google Gemini API
-   **Comunicação / API:** Twilio API for WhatsApp
-   **Análise de Dados:** Pandas
-   **Testes Locais:** Ngrok (para expor o servidor local à internet)
