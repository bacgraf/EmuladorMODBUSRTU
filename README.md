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
- ✅ Suporte a resolução (valores decimais)
- ✅ Offset automático Base0/Base1
- ✅ Conversão automática vírgula→ponto
- ✅ Multiprocessing para liberação rápida de porta COM

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

## 🔨 Compilar Executável

Para gerar um executável standalone (sem necessidade de Python instalado):

```bash
build.bat
```

O executável será criado em `dist\EmuladorMODBUSRTU\EmuladorMODBUSRTU.exe`

Veja [BUILD.md](BUILD.md) para instruções detalhadas.

## 📖 Como Usar

1. **Executar o emulador**
   ```bash
   python main.py
   ```
   
   Ou use o executável compilado (se disponível).

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
├── 1.0.0/
│   ├── src/
│   │   ├── main.py                      # Interface PyQt6
│   │   ├── csv_parser.py                # Parser de CSV
│   │   ├── csv_editor.py                # Editor de CSV
│   │   ├── config.py                    # Gerenciador de configurações
│   │   ├── modbus_server_multiprocess.py # Servidor Modbus (multiprocessing)
│   │   └── requirements.txt             # Dependências Python
│   ├── docs/
│   │   └── Mapa_de_memoria_BMS.csv      # Exemplo de mapa
│   ├── RESOLUCAO_E_OFFSET.md            # Doc resolução e offset
│   └── build.spec                       # Config PyInstaller
├── Documentação/
│   ├── Mapa_de_memoria_TPS.csv          # Mapa TPS
│   └── Mapa_de_memoria_BMS.csv          # Mapa BMS
├── README.md                            # Este arquivo
├── BUILD.md                             # Guia de compilação
└── PROBLEMA_PORTA_COM.md                # Doc troubleshooting
```

## 🛠️ Desenvolvimento

### Arquitetura Multiprocessing

- **Processo Principal**: Interface PyQt6
- **Processo Servidor**: Servidor Modbus RTU isolado
- **Shared Memory**: Comunicação via mp.Array
- **Polling**: Atualização UI a cada 100ms

### Vantagens do Multiprocessing

- ✅ Liberação rápida de porta COM (2-5 segundos)
- ✅ Isolamento total entre UI e servidor
- ✅ process.kill() força Windows a liberar recursos
- ✅ Sem travamentos na UI

### Resolução e Offset

- **Resolução**: Converte valores reais ↔ valores Modbus
  - Exemplo: 12.34V com resolução 0.01 = 1234 no Modbus
- **Offset +1**: Compensa conversão Base1→Base0 do cliente
  - UI Base0=201 → Armazena em 202 → Cliente lê corretamente

Veja [RESOLUCAO_E_OFFSET.md](1.0.0/RESOLUCAO_E_OFFSET.md) para detalhes.

### Tratamento de Erros

- Validação de porta serial ANTES de criar servidor
- Monitoramento de liberação de porta (timeout 2 minutos)
- Captura de exceções em processos com signal PyQt6
- Mensagens de erro exibidas ao usuário

## 📊 Mapa de Memória

O arquivo CSV deve ter as seguintes colunas:
- `Tipo`: COIL, DISC, IREG ou HREG
- `RegBase0`: Endereço base 0
- `RegBase1`: Endereço base 1
- `Objeto`: Nome do registrador
- `Unidade`: Unidade de medida (V, A, Hz, etc.)
- `Resolucao`: Fator de conversão (0.01, 0.1, 1)
- `Permissao`: R (read) ou R/W (read/write)
- `FCs`: Funções Modbus suportadas
- `ValorInicial`: Valor inicial (número ou ON/OFF)
- `Descricao`: Descrição do registrador

### Exemplo de CSV

```csv
Tipo,RegBase0,RegBase1,Objeto,Unidade,Resolucao,Permissao,FCs,Intervalo,ValorInicial,Descricao
IREG,300,30301,tensao_retificador,V,0.01,R,4,,,Tensao do retificador
IREG,69,30070,frequencia,Hz,0.1,R,4,,,Frequencia da rede
DISC,201,10202,Teste_Din_bit1,none,1,R,2,,,Entrada digital bit 1
COIL,208,209,Teste_Dout_pri_bit0,none,1,R/W,1/5,,OFF,Saida digital primaria bit 0
```

Veja [RESOLUCAO_E_OFFSET.md](1.0.0/RESOLUCAO_E_OFFSET.md) para detalhes sobre resolução e offset.

## 🐛 Tratamento de Erros

O emulador captura e exibe erros para:
- Porta COM em uso
- Slave ID inválido
- CSV não encontrado
- Problemas de threading
- Erros de comunicação Modbus

## 📝 Changelog

### v1.0.0 (2025-01-16)
- ✅ Interface PyQt6 moderna e responsiva
- ✅ Servidor Modbus RTU Serial com multiprocessing
- ✅ Carregamento dinâmico de mapa de memória CSV
- ✅ Suporte a resolução para valores decimais
- ✅ Offset automático Base0/Base1
- ✅ Conversão automática vírgula→ponto
- ✅ Liberação rápida de porta COM (2-5s)
- ✅ Monitoramento de porta com timeout
- ✅ Editor de CSV integrado
- ✅ Tratamento robusto de erros
- ✅ Logs detalhados com debug

## 📄 Licença

Este projeto está licenciado sob a licença MIT.

## 👨‍💻 Autor

Marcel Hilleshein

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no GitHub.

---

**Status:** ✅ Pronto para Produção

