# Use a imagem base oficial do Python 3.12 na versão slim para reduzir o tamanho da imagem final
FROM python:3.12-slim

# Define variáveis de ambiente para otimizar o Python
# PYTHONDONTWRITEBYTECODE=1: Evita que o Python grave arquivos .pyc no disco
# PYTHONUNBUFFERED=1: Permite que os logs do Python sejam enviados diretamente para o terminal sem buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do container
WORKDIR /app

# (Opcional) Instala dependências do sistema caso os pacotes de machine learning precisem (ex: libGL para OpenCV)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc libgl1-mesa-glx libglib2.0-0 \
#     && rm -rf /var/lib/apt/lists/*

# Copia APENAS o requirements.txt primeiro. 
# Isso permite que o Docker faça cache dessa camada e não reinstale as dependências toda vez que o código fonte mudar
COPY requirements.txt .

# Instala as dependências listadas no requirements.txt
# --no-cache-dir instrui o pip a não salvar o cache dos pacotes baixados, mantendo a imagem menor
RUN pip install --no-cache-dir -r requirements.txt

# Caso o gunicorn não esteja no seu requirements.txt, descomente a linha abaixo para instalá-lo
# RUN pip install --no-cache-dir gunicorn

# Copia todo o restante do código do seu projeto para o diretório de trabalho do container
COPY . .

# Expõe a porta 8080 para o mundo externo (Porta padrão esperada pelo Google Cloud Run)
EXPOSE 8080

# Comando para iniciar o servidor em produção usando o Gunicorn
# 'app:app' refere-se a <nome_do_arquivo>:<nome_da_instancia_flask>
# Exemplo: se seu arquivo principal for 'main.py', mude para 'main:app'
# O Cloud Run requer que a aplicação escute em 0.0.0.0 e responda na porta definida pela variável $PORT (ou 8080 como fallback)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
