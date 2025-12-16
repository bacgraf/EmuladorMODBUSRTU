# 🔋 EmuladorMODBUSRTU

Emulador de Sistema de Gerenciamento de Bateria (BMS) com interface gráfica PyQt6 e protocolo Modbus RTU Serial.

## 📋 Descrição

Este projeto implementa um emulador de BMS (Battery Management System) que permite:
- Interface gráfica moderna com PyQt6
- Servidor Modbus RTU Serial
- Carregamento dinâmico de mapa de memória via CSV
- Simulação de Coils, Discrete Inputs, Input Registers e Holding Registers
- Suporte a Broadcast (Slave ID 0) e Slave ID customizável (1-247)

## 🚀 Funcionalidades

- ✅ Interface gráfica intuitiva
- ✅ Carregamento de mapa de memória (CSV)
- ✅ Editor de mapa de memória integrado
- ✅ Servidor Modbus em tempo real
- ✅ Configuração de porta serial (COM)
- ✅ Suporte a diferentes baudrates e configurações
- ✅ Monitoramento em tempo real de registradores
- ✅ Tratamento robusto de erros
- ✅ Logs detalhados no console

## 📦 Requisitos

- Python 3.8+
- PyQt6 >= 6.4.0
- pymodbus >= 3.0.0
- pyserial >= 3.5

## 🔧 Instalação

1. **Clonar repositório**
   ```bash
   git clone https://github.com/seu-usuario/EmuladorMODBUSRTU.git
   cd EmuladorMODBUSRTU
   ```

2. **Criar ambiente virtual**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Como Usar

1. **Executar o emulador**
   ```bash
   python main.py
   ```

2. **Carregar mapa de memória**
   - Clique em "Selecionar..." e escolha o arquivo CSV
   - O mapa será carregado e exibido nos abas

3. **Configurar servidor**
   - Selecione a porta COM (ex: COM16)
   - Defina baudrate, data bits, paridade, stop bits
   - Digite o Slave ID (1-247)

4. **Iniciar servidor**
   - Clique em "Iniciar Servidor"
   - Status mudará para 🟢 Rodando

5. **Interagir com os dados**
   - Coils: Clique para ON/OFF
   - Discrete Inputs: Clique para ON/OFF
   - Input Registers: Digite valores
   - Holding Registers: Digite valores

## 📁 Estrutura do Projeto

```
EmuladorMODBUSRTU/
├── main.py                          # Interface principal
├── csv_parser.py                    # Parser de CSV
├── csv_editor.py                    # Editor de CSV
├── bms_emulator.py                  # Lógica de emulação
├── requirements.txt                 # Dependências
├── .gitignore                       # Arquivo Git ignore
├── Documentação/
│   ├── Mapa_de_memoria_BMS.csv      # Mapa de memória
│   └── EspecificacaoTecnica.md      # Documentação técnica
├── funcional/                       # Versão funcional
└── prototipo/                       # Protótipo inicial
```

## 🛠️ Desenvolvimento

### Estrutura de Threads

- **ServerThread**: Executa `serve_forever()` do Modbus
- **MonitorThread**: Atualiza UI com valores dos registradores

### Tratamento de Erros

- Validação de porta serial ANTES de criar servidor
- Captura de exceções em threads com signal PyQt6
- Mensagens de erro exibidas ao usuário

## 📊 Mapa de Memória

O arquivo CSV deve ter as seguintes colunas:
- `tipo`: COIL, DI, IR ou HR
- `base0`: Endereço base 0
- `base1`: Endereço base 1
- `nome`: Nome do registrador
- `unidade`: Unidade de medida
- `valor_inicial`: Valor inicial

## 🐛 Tratamento de Erros

O emulador captura e exibe erros para:
- Porta COM em uso
- Slave ID inválido
- CSV não encontrado
- Problemas de threading
- Erros de comunicação Modbus

## 📝 Changelog

### v1.0.0 (2025-01-16)
- ✅ Primeira versão com interface PyQt6
- ✅ Suporte a Modbus RTU Serial
- ✅ Carregamento de CSV dinâmico
- ✅ Tratamento robusto de erros

## 📄 Licença

Este projeto está licenciado sob a licença MIT.

## 👨‍💻 Autor

Marcel Hilleshein

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no GitHub.

---

**Status:** ✅ Pronto para Produção

