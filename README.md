# Gerador de APK a partir de AAB

Um aplicativo web simples para converter arquivos Android App Bundle (.aab) em arquivos APK (.apk) usando o bundletool do Google.

## 🚀 Funcionalidades

- Interface web simples e intuitiva
- Upload de arquivos .aab
- Conversão automática para APK universal
- Download direto do APK gerado
- Suporte a arquivos de até 200MB

## 📋 Pré-requisitos

### Software necessário:
- **Python 3.7+**
- **Java 8+** (necessário para o bundletool)
- **Android Keystore** (.jks) para assinatura

### Arquivos necessários:
- **bundletool-all-X.X.X.jar** - [Download aqui](https://github.com/google/bundletool/releases)
- **Keystore Android** (.jks) - Para assinar o APK

## 🛠️ Instalação

1. **Clone ou baixe o projeto:**
```bash
git clone <seu-repositorio>
cd GeradorDeApk-desktop
```

2. **Instale as dependências Python:**
```bash
pip install fastapi uvicorn python-multipart
```

3. **Configure os caminhos no server.py:**
```python
BUNDLETOOL_JAR = r"C:\Users\salle\Downloads\bundletool-all-1.18.2.jar"
KEYSTORE_PATH = r"C:\Users\salle\Downloads\meu-keystore.jks"
KEYSTORE_PASS = "sua-senha-keystore"
KEY_ALIAS = "seu-alias"
KEY_PASS = "sua-senha-chave"
```

## 🚀 Como usar

1. **Inicie o servidor:**
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 3002
```

2. **Acesse no navegador:**
```
http://localhost:3002
```

3. **Faça o upload do arquivo .aab e aguarde a conversão**

## 📁 Estrutura do projeto

```
GeradorDeApk-desktop/
├── server.py          # Servidor FastAPI backend
├── index.html         # Interface web frontend  
└── README.md          # Este arquivo
```

## 🔧 Configuração

### Ajustar caminhos no server.py:

```python
# Caminho para o bundletool JAR
BUNDLETOOL_JAR = r"C:\caminho\para\bundletool-all-1.18.2.jar"

# Configurações do keystore
KEYSTORE_PATH = r"C:\caminho\para\seu-keystore.jks"
KEYSTORE_PASS = "sua-senha"
KEY_ALIAS = "seu-alias"  
KEY_PASS = "senha-da-chave"

# Tamanho máximo de upload (200MB)
MAX_UPLOAD_SIZE = 200 * 1024 * 1024
```

### Criar um Keystore (se não tiver):

```bash
keytool -genkey -v -keystore meu-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias meu-alias
```

## 🐛 Solução de problemas

### Erro "Java não encontrado"
- Verifique se o Java está instalado: `java -version`
- Adicione o Java ao PATH do sistema

### Erro "Keystore não encontrado"
- Verifique se o caminho do keystore está correto
- Certifique-se que as senhas estão corretas

### Erro "Failed to fetch"
- Verifique se o servidor está rodando
- Confirme se está acessando a porta correta (3002)

### Erro "Bundletool failed"
- Verifique se o arquivo .aab é válido
- Confirme se o bundletool JAR está na versão correta

## 📝 Logs e Debug

O servidor exibe logs detalhados no terminal, incluindo:
- Status do upload
- Comandos executados
- Arquivos gerados
- Erros encontrados

## 🔒 Segurança

⚠️ **Importante para produção:**
- Altere `allow_origins=["*"]` para domínios específicos
- Use HTTPS em produção
- Proteja o keystore com senhas fortes
- Limite o tamanho de upload conforme necessário

## 🛡️ Limitações

- Arquivos .aab limitados a 200MB (configurável)
- Apenas APKs universais são gerados
- Requer keystore válido para assinatura

## 📄 Licença

Este projeto é livre para uso pessoal e educacional.

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Enviar pull requests

---

**Desenvolvido com FastAPI e bundletool**
