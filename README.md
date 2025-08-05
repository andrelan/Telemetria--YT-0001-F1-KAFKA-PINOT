# 🏎️ Painel de Telemetria F1 em Tempo Real

YouTube >> https://www.youtube.com/watch?v=89T0rjvfIvc

## 🛠️ Stack Tecnológica

- **Visualização**: Streamlit
- **Olap Datastore**: Apache Pinot
- **Message Broker**: Apache Kafka
- **Containerização**: Docker
- **Linguagem**: python

## 📋 Pré-requisitos

- Docker e Docker Compose
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (Instalador moderno de pacotes Python)

## 🚀 Começando

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositório>
   cd f1-realtime
   ```

3. **Inicie a infraestrutura**
   ```bash
   docker-compose up -d
   ```
   Isso iniciará:
   - Broker Kafka
   - Kafka UI
   - Pinot Zookeeper
   - Pinot Controller
   - Pinot Broker
   - Pinot Server

4. **Inicie a ingestão de dados**
   ```bash
   cd src
   uv run f1_live_timing.py
   ```

5. **Crie o schema e a tabela no Pinot**
   ```bash
   cd src
   cd pinot
   ./restart.sh
   ```

6. **Execute o painel**
   ```bash
   cd .. # volta para a raiz do projeto
   uv run streamlit run dash.py
   ```

6. **Acesse o painel**
   - Abra seu navegador e acesse `http://localhost:8501`


## 🔧 Configuração

- Kafka UI: `http://localhost:8080`
- Pinot Controller: `http://localhost:9000`
- Pinot Swagger: `http://localhost:9000/help#/`
