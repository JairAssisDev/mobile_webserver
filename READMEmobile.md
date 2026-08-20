# Mobile-First Inference Web Server (Flask)

Este repositório contém uma versão otimizada e simplificada do servidor web, projetada especificamente para ser acessada via smartphones e dispositivos móveis (Mobile-First). Diferente do servidor principal, que se integra via hardware com o ESP32-CAM, esta versão é focada no upload direto de fotos da galeria ou da câmera do próprio celular.

## 🚀 Como Instalar e Rodar

### Pré-requisitos
- **Python 3.8+**
- Modelos treinados (`binary.pt`, `benign.pt`, `malignant.pt`) localizados na pasta `models/` deste diretório.

### Passo a Passo

1. **Abra o terminal** na pasta do projeto (`mobile_webserver`).
2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv env
   ```
3. **Ative o ambiente virtual:**
   - No Windows: `.\env\Scripts\activate`
   - No Linux/Mac: `source env/bin/activate`
4. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Caso não exista, as principais dependências são: `flask ultralytics pillow numpy opencv-python`)*
5. **Execute o servidor:**
   ```bash
   python app.py
   ```
6. **Acesse no Celular (ou Navegador):**
   - Na máquina local: Abra `http://localhost:5001`
   - Pelo celular (na mesma rede Wi-Fi): Abra `http://<IP_DA_SUA_MAQUINA>:5001` (ex: `http://192.168.1.100:5001`)

---

## 🔬 Fluxo de Processamento e Inferência (Ponta a Ponta)

O motor central compartilha a mesma inteligência do servidor principal (Cascata), mas com um fluxo de aquisição de imagens mais direto e simplificado.

### 1. Inicialização (Boot)
Quando o servidor Flask é iniciado (`python app.py`), ele pré-carrega o modelo primário (`binary.pt`) na RAM. O servidor é exposto na porta **5001** para evitar conflitos com o servidor principal ESP32.

### 2. Aquisição da Imagem via Dispositivo Móvel
Nesta arquitetura, a imagem é fornecida ativamente pelo usuário final:
- A interface web utiliza APIs HTML5 nativas (como `<input type="file" accept="image/*" capture="camera">`) para abrir a câmera do smartphone do usuário ou sua galeria de fotos.
- Após a seleção/captura, a imagem é convertida em um formato `Base64` no lado do cliente.
- O payload é enviado para o servidor via requisição `POST` para a rota `/api/predict`.

### 3. Pré-Processamento (Decoding)
Os dados brutos recebidos são preparados para a inteligência artificial:
- O Base64 é decodificado, interpretado pela biblioteca **Pillow (PIL)** e convertido para o espectro de cores `RGB`.
- Em seguida, é transformado em um array matricial do **NumPy**, alimentando o motor de visão computacional da arquitetura YOLO.

### 4. Pipeline de Classificação em Cascata
Exatamente como no módulo principal, o modelo utiliza uma arquitetura especialista para melhor precisão:
- **Estágio 1 (Decisão Primária):** O modelo `binary.pt` analisa o tecido e decreta se é `BENIGNO` ou `MALIGNO`.
- **Estágio 2 (Sub-especialista):** 
  - Se for Benigno, o modelo `benign.pt` é carregado e acionado para descobrir o subtipo (ex: Nevo).
  - Se for Maligno, o modelo `malignant.pt` entra em ação para descobrir se é Melanoma, etc.
- O sistema de cache (Lazy Loading) mantém os modelos em memória após o primeiro uso, acelerando as consultas seguintes.

### 5. Resposta Visual
- O servidor compila os resultados (classes identificadas e percentuais de confiança matemática) em um JSON.
- A interface mobile recebe a resposta e atualiza dinamicamente, mostrando o diagnóstico para o usuário final em um layout limpo, responsivo e amigável ao toque (touch-friendly).
