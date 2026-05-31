# CuidaFácil — Streamlit Cloud + Google Sheets + GA4

Aplicativo responsivo para cadastro por e-mail, criação e conclusão de atividades, progresso do usuário e área Admin com métricas de produto.

## Funcionalidades

- Login simples por nome e e-mail
- Tela de configuração inicial
- Cadastro de atividades
- Conclusão de atividades
- Progresso do usuário
- Dashboard Admin com cards, funil e retenção D1/D7/D30
- Integração Google Sheets via `sheets_repository.py`
- Integração Google Analytics 4 via Measurement Protocol
- Deploy pronto para Streamlit Community Cloud
- Provérbios em `assets/proverbios.json`, sem gravar no banco

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Como configurar

Copie:

```text
.streamlit/secrets.example.toml
```

para:

```text
.streamlit/secrets.toml
```

Preencha o `spreadsheet_id`, as credenciais da Service Account e, se quiser, as chaves do GA4.

## Abas do Google Sheets

Você só precisa criar uma planilha vazia no Google Sheets. O app cria/valida automaticamente as abas:

- usuarios
- atividades
- execucoes
- sessoes
- eventos_uso

Compartilhe a planilha com o `client_email` da Service Account como **Editor**.

## Admin

A aba Admin aparece quando o e-mail usado no login for igual ao valor de:

```toml
admin_email = "admin@cuidafacil.com"
```

## Streamlit Community Cloud

1. Suba este projeto para o GitHub.
2. Crie o app no Streamlit Cloud apontando para `app.py`.
3. Em **App > Settings > Secrets**, cole o conteúdo do seu `secrets.toml`.
4. Faça o deploy.


## Ajustes de performance

Esta versão evita que todas as telas sejam processadas ao mesmo tempo. A navegação usa `st.radio` no menu lateral, em vez de `st.tabs`, porque `st.tabs` executa o conteúdo de todas as abas a cada recarregamento.

Também há cache de leitura do Google Sheets com TTL de 45 segundos em `services/app_service.py`. Após gravações, o cache é limpo automaticamente.
