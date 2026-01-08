# 📘 Manual do Usuário - Emulador MODBUS RTU v1.0.0

## 📋 Índice
1. [Introdução](#introdução)
2. [Requisitos do Sistema](#requisitos-do-sistema)
3. [Instalação](#instalação)
4. [Iniciando o Software](#iniciando-o-software)
5. [Carregando Mapa de Memória](#carregando-mapa-de-memória)
6. [Configurando Comunicação Serial](#configurando-comunicação-serial)
7. [Iniciando o Servidor Modbus](#iniciando-o-servidor-modbus)
8. [Interagindo com Registradores](#interagindo-com-registradores)
9. [Editor de Mapa de Memória](#editor-de-mapa-de-memória)
10. [Permissões de Acesso](#permissões-de-acesso)
11. [Resolução e Valores Decimais](#resolução-e-valores-decimais)
12. [Solução de Problemas](#solução-de-problemas)

---

## 🎯 Introdução

O **Emulador MODBUS RTU** é um software que simula um dispositivo escravo Modbus RTU através de comunicação serial (RS-232/RS-485). Ele permite:

- ✅ Emular um BMS (Battery Management System) ou qualquer dispositivo Modbus
- ✅ Configurar mapas de memória personalizados via arquivo CSV
- ✅ Suportar Coils, Discrete Inputs, Input Registers e Holding Registers
- ✅ Controlar permissões de leitura/escrita por registrador
- ✅ Trabalhar com valores decimais usando resolução
- ✅ Responder a comandos Modbus de um Master/Cliente

---

## 💻 Requisitos do Sistema

### Mínimos
- **Sistema Operacional**: Windows 10 ou superior
- **Memória RAM**: 2 GB
- **Espaço em Disco**: 200 MB
- **Porta Serial**: COM física ou virtual (USB-Serial)

### Recomendados
- **Sistema Operacional**: Windows 10/11 64-bit
- **Memória RAM**: 4 GB ou mais
- **Conversor USB-Serial**: CH340, FTDI, ou similar

---

## 📦 Instalação

### Versão Executável (Recomendado)
1. Extraia o arquivo `EmuladorMODBUSRTU.zip`
2. Execute `EmuladorMODBUSRTU.exe`
3. Não é necessário instalar Python ou dependências

### Versão Python (Desenvolvimento)
```bash
# Clonar repositório
git clone <repositório>
cd EmuladorMODBUSRTU

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar
python main.py
```

---

## 🚀 Iniciando o Software

1. **Execute** `EmuladorMODBUSRTU.exe`
2. Aguarde o **splash screen** (2 segundos)
3. A janela principal será exibida maximizada

### Primeira Execução
Na primeira execução, você verá uma mensagem:
> "Selecione um Mapa de Memória para começar"

Clique em **OK** e prossiga para carregar um mapa de memória.

---

## 📄 Carregando Mapa de Memória

### Passo 1: Selecionar Arquivo CSV
1. Clique no botão **"Selecionar..."** na seção "📄 Mapa de Memória"
2. Navegue até o arquivo CSV do mapa de memória
3. Selecione o arquivo (ex: `Mapa_de_memoria_BMS.csv`)
4. Clique em **Abrir**

### Passo 2: Verificar Carregamento
Após carregar, você verá:
- ✅ Caminho do arquivo no campo de texto
- ✅ Abas preenchidas com registradores (Coils, Discrete Inputs, etc.)
- ✅ Mensagem de sucesso com total de registradores

### Formato do Arquivo CSV
O arquivo CSV deve conter as seguintes colunas:

```csv
Tipo,RegBase0,RegBase1,Objeto,Unidade,Resolucao,Permissao,FCs,Intervalo,ValorInicial,Descricao
COIL,208,209,Saida_Digital_0,none,1,R/W,1/5,,OFF,Saída digital 0
DISC,201,10202,Entrada_Digital_1,none,1,R,2,,,Entrada digital 1
IREG,300,30301,Tensao_Bateria,V,0.01,R,4,,,Tensão da bateria
HREG,400,40401,Corrente_Carga,A,0.1,R/W,3/6/16,,,Corrente de carga
```

**Colunas:**
- `Tipo`: COIL, DISC, IREG, HREG
- `RegBase0`: Endereço base 0 (usado internamente)
- `RegBase1`: Endereço base 1 (referência Modbus)
- `Objeto`: Nome do registrador
- `Unidade`: Unidade de medida (V, A, Hz, etc.)
- `Resolucao`: Fator de conversão (0.01, 0.1, 1)
- `Permissao`: R (leitura), R/W (leitura/escrita), R/W/B (com broadcast)
- `FCs`: Funções Modbus suportadas
- `ValorInicial`: Valor inicial (número ou ON/OFF)
- `Descricao`: Descrição do registrador

---

## ⚙️ Configurando Comunicação Serial

### Parâmetros Disponíveis

1. **Porta**: Selecione a porta COM (ex: COM3, COM16)
   - O software detecta automaticamente portas disponíveis
   
2. **Baudrate**: Taxa de transmissão
   - Opções: 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200
   - Padrão: 19200
   
3. **Data Bits**: Bits de dados
   - Opções: 5, 6, 7, 8
   - Padrão: 8
   
4. **Paridade**: Controle de paridade
   - Opções: None, Even, Odd, Mark, Space
   - Padrão: None
   
5. **Stop Bits**: Bits de parada
   - Opções: 1, 2
   - Padrão: 1
   
6. **Slave ID**: Identificador do escravo Modbus
   - Faixa: 1 a 247
   - Padrão: 1
   - **Nota**: O emulador também responde ao Slave ID 0 (broadcast)

### Configuração Típica
```
Porta: COM3
Baudrate: 19200
Data Bits: 8
Paridade: None
Stop Bits: 1
Slave ID: 1
```

---

## ▶️ Iniciando o Servidor Modbus

### Passo 1: Verificar Configurações
1. Certifique-se de que o **mapa de memória está carregado**
2. Verifique se a **porta COM está disponível**
3. Confirme os **parâmetros seriais**

### Passo 2: Iniciar Servidor
1. Clique no botão **"Iniciar Servidor"**
2. Aguarde a mensagem de sucesso
3. O status mudará para **🟢 Rodando (ID X)**

### Passo 3: Verificar Funcionamento
- Status: **🟢 Rodando**
- Botão muda para: **"Parar Servidor"**
- Configurações ficam desabilitadas
- Registradores ficam disponíveis para interação

### Parar Servidor
1. Clique no botão **"Parar Servidor"**
2. Aguarde a liberação da porta (2-5 segundos)
3. Status mudará para **⚪ Parado**

---

## 🎛️ Interagindo com Registradores

### Abas Disponíveis

#### 1️⃣ Coils (01/05) - Saídas Digitais
- **Função Modbus**: 01 (Read), 05 (Write Single), 15 (Write Multiple)
- **Valores**: ON/OFF
- **Interação**: Clique no botão para alternar entre ON (verde) e OFF (cinza)
- **Cor**: 
  - 🟢 Verde = ON
  - ⚫ Cinza = OFF

#### 2️⃣ Discrete Inputs (02) - Entradas Digitais
- **Função Modbus**: 02 (Read)
- **Valores**: ON/OFF
- **Interação**: Clique no botão para simular entrada
- **Cor**:
  - 🔴 Vermelho = ON
  - ⚫ Cinza = OFF

#### 3️⃣ Input Registers (04) - Registradores de Entrada
- **Função Modbus**: 04 (Read)
- **Valores**: 0 a 65535 (16-bit)
- **Interação**: Digite o valor no campo e pressione Enter
- **Resolução**: Valores são convertidos automaticamente
  - Exemplo: Digite 12.34V com resolução 0.01 → Armazena 1234

#### 4️⃣ Holding Registers (03/06/16) - Registradores de Retenção
- **Função Modbus**: 03 (Read), 06 (Write Single), 16 (Write Multiple)
- **Valores**: 0 a 65535 (16-bit)
- **Interação**: Digite o valor no campo e pressione Enter
- **Resolução**: Valores são convertidos automaticamente

### Exemplo de Uso
```
1. Vá para aba "Coils (01/05)"
2. Localize "Saida_Digital_0"
3. Clique no botão para mudar de OFF para ON
4. O Master Modbus verá o valor 1 ao ler este coil
```

---

## ✏️ Editor de Mapa de Memória

### Abrindo o Editor
1. Clique no botão **"✏️ Editar Mapa"**
2. O editor abrirá em uma nova janela
3. Se houver um mapa carregado, ele será exibido automaticamente

### Funcionalidades do Editor

#### Adicionar Registrador
1. Clique em **"➕ Adicionar Linha"**
2. Preencha os campos:
   - Tipo: COIL, DISC, IREG, HREG
   - RegBase0: Endereço base 0
   - RegBase1: Endereço base 1
   - Objeto: Nome do registrador
   - Unidade: V, A, Hz, etc.
   - Resolução: 0.01, 0.1, 1
   - Permissão: R, R/W, R/W/B
   - Valor Inicial: Número ou ON/OFF

#### Remover Registrador
1. Selecione a linha desejada
2. Clique em **"➖ Remover Linha"**

#### Salvar Alterações
1. Clique em **"💾 Salvar"**
2. Escolha o local e nome do arquivo
3. O mapa será recarregado automaticamente

#### Novo Mapa
1. Clique em **"📄 Novo"**
2. O editor será limpo
3. Adicione registradores conforme necessário

---

## 🔐 Permissões de Acesso

O emulador valida permissões de escrita no lado do servidor.

### Tipos de Permissão

#### 🔵 R (Somente Leitura)
- Master pode **apenas ler** o valor
- Tentativas de escrita são **bloqueadas**
- Cor do nome: **Azul**
- Exemplo: Sensores, medições

#### 🟢 R/W (Leitura/Escrita)
- Master pode **ler e escrever**
- Escritas são **permitidas**
- Cor do nome: **Verde**
- Exemplo: Setpoints, configurações

#### 🟡 R/W/B (Leitura/Escrita/Broadcast)
- Master pode **ler, escrever e usar broadcast**
- Responde ao Slave ID 0
- Cor do nome: **Amarelo**
- Exemplo: Comandos globais

### Validação de Permissões
Quando o Master tenta escrever em um registrador somente leitura:
```
❌ BLOQUEADO: Escrita em endereço 300 somente leitura (Permissão: R)
```

---

## 🔢 Resolução e Valores Decimais

### O que é Resolução?
A resolução converte valores reais em valores Modbus (inteiros de 16-bit).

### Fórmula
```
Valor Modbus = Valor Real / Resolução
Valor Real = Valor Modbus × Resolução
```

### Exemplos

#### Tensão (Resolução 0.01)
```
Valor Real: 12.34 V
Resolução: 0.01
Valor Modbus: 12.34 / 0.01 = 1234
```

#### Corrente (Resolução 0.1)
```
Valor Real: 5.6 A
Resolução: 0.1
Valor Modbus: 5.6 / 0.1 = 56
```

#### Frequência (Resolução 0.01)
```
Valor Real: 60.00 Hz
Resolução: 0.01
Valor Modbus: 60.00 / 0.01 = 6000
```

### Conversão Automática
O emulador faz a conversão automaticamente:
- **Na UI**: Digite valores reais (12.34)
- **No Modbus**: Armazena valores inteiros (1234)
- **Vírgula → Ponto**: Conversão automática (12,34 → 12.34)

---

## 🔧 Solução de Problemas

### Porta COM em Uso
**Problema**: "Porta COM3 ainda está em uso"

**Solução**:
1. Feche outros programas que usam a porta
2. Aguarde 5-10 segundos
3. Tente novamente
4. Se persistir, reinicie o computador

### Porta COM Não Aparece
**Problema**: Porta COM não está na lista

**Solução**:
1. Verifique se o conversor USB-Serial está conectado
2. Instale os drivers do conversor (CH340, FTDI, etc.)
3. Verifique no Gerenciador de Dispositivos do Windows
4. Reinicie o software

### Mapa de Memória Não Carrega
**Problema**: Erro ao carregar CSV

**Solução**:
1. Verifique se o arquivo está no formato correto
2. Certifique-se de que todas as colunas estão presentes
3. Verifique se não há linhas vazias
4. Use o editor integrado para criar um novo mapa

### Master Não Conecta
**Problema**: Master não consegue ler registradores

**Solução**:
1. Verifique se o Slave ID está correto
2. Confirme os parâmetros seriais (baudrate, paridade, etc.)
3. Teste com outro software Modbus (Modbus Poll, QModMaster)
4. Verifique o cabeamento RS-485 (A, B, GND)

### Valores Incorretos
**Problema**: Valores lidos estão errados

**Solução**:
1. Verifique a resolução no CSV
2. Confirme se o Master está usando a mesma resolução
3. Verifique o offset Base0/Base1
4. Use o editor para corrigir o mapa

### Servidor Não Para
**Problema**: Botão "Parar Servidor" não funciona

**Solução**:
1. Aguarde até 2 minutos (timeout automático)
2. Feche o software
3. Abra o Gerenciador de Tarefas
4. Finalize processos "EmuladorMODBUSRTU"


---

## 📝 Notas Importantes

1. **Backup**: Sempre faça backup dos mapas de memória CSV
2. **Permissões**: Configure permissões adequadas para segurança
3. **Resolução**: Documente a resolução usada para cada registrador
4. **Slave ID**: Use IDs únicos para cada dispositivo na rede
5. **Porta Serial**: Libere a porta antes de usar em outro software

---

## ✅ Checklist de Uso Rápido

- [ ] Software instalado/extraído
- [ ] Mapa de memória CSV preparado
- [ ] Porta COM identificada
- [ ] Parâmetros seriais configurados
- [ ] Mapa de memória carregado
- [ ] Servidor iniciado com sucesso
- [ ] Master conectado e comunicando
- [ ] Valores sendo lidos/escritos corretamente

---

**Versão do Manual**: 1.0.0  
**Data**: Janeiro 2026  
**Software**: Emulador MODBUS RTU v1.0.0
