# 📐 Resolução e Offset Base0/Base1

## 🎯 Resumo

Este documento explica como o EmuladorMODBUSRTU implementa:
1. **Resolução** - Conversão entre valores reais e valores Modbus
2. **Offset +1** - Compensação da conversão Base1→Base0 do cliente Modbus

---

## 📊 Resolução

### O que é?

A resolução define quantas casas decimais um valor possui. É usada para converter valores reais (com decimais) em valores inteiros que o Modbus pode transmitir.

### Como funciona?

**Fórmula:**
```
Valor Modbus = Valor Real / Resolução
Valor Real = Valor Modbus × Resolução
```

### Exemplos

| Valor Real | Resolução | Valor Modbus | Explicação |
|------------|-----------|--------------|------------|
| 12.34 V    | 0.01      | 1234         | 12.34 / 0.01 = 1234 |
| 60.5 Hz    | 0.1       | 605          | 60.5 / 0.1 = 605 |
| 220.0 V    | 0.1       | 2200         | 220.0 / 0.1 = 2200 |
| 1 (bit)    | 1         | 1            | 1 / 1 = 1 |

### Implementação no Código

**Ao enviar para Modbus (UI → Modbus):**
```python
def update_ir(self, addr, value):
    resolucao = float(self.ir_map[addr].get('resolucao', 1))
    value = value.replace(',', '.')  # Aceita vírgula
    valor_modbus = int(float(value) / resolucao)
    self.modbus.set_value(4, addr + 1, valor_modbus)
```

**Ao receber do Modbus (Modbus → UI):**
```python
def on_ir_changed(self, addr, value):
    resolucao = float(self.ir_map[addr].get('resolucao', 1))
    valor_real = value * resolucao
    entry.setText(str(valor_real))
```

### Conversão Automática de Vírgula

O sistema aceita tanto vírgula quanto ponto como separador decimal:
- Usuário digita: `12,34` → Sistema converte para: `12.34`
- Conversão acontece em tempo real no campo de entrada

---

## 🔢 Offset Base0/Base1

### O Problema

O protocolo Modbus tem duas convenções de endereçamento:
- **Base0**: Endereços começam em 0 (usado internamente)
- **Base1**: Endereços começam em 1 (usado em documentação)

**Exemplo:**
- CSV mostra: Base0=201, Base1=202
- Cliente Modbus pede Base1=202
- Protocolo transmite: 0x00C9 (201 em Base0)

### A Solução: Offset +1

Para compensar a conversão automática do cliente, o servidor armazena valores com offset +1:

```
UI mostra Base0=201
↓
Sistema armazena em endereço 202 (201+1)
↓
Cliente pede Base1=202 (vira 201 no protocolo)
↓
Servidor retorna valor do endereço 202
✅ Valor correto!
```

### Implementação no Código

**Ao escrever (UI → Modbus):**
```python
def toggle_di(self, addr, btn, checked):
    # addr = 201 (Base0 da UI)
    # Armazena em addr+1 = 202
    self.modbus.set_value(2, addr + 1, 1 if checked else 0)
```

**Ao ler (Modbus → UI):**
```python
def poll_shared_memory(self):
    for addr in self.di_map.keys():
        # addr = 201 (Base0 da UI)
        # Lê de addr+1 = 202
        val = self.modbus.get_value(2, addr + 1)
        self.on_di_changed(addr, bool(val))
```

### Trace Modbus Real

**Sem offset (ERRADO):**
```
UI: Clique em Base0=201
Sistema: Armazena em 201
Cliente: Pede Base1=202 → Protocolo envia 0x00C9 (201)
Resultado: ❌ Lê endereço errado (201 em vez de 202)
```

**Com offset +1 (CORRETO):**
```
UI: Clique em Base0=201
Sistema: Armazena em 202 (201+1)
Cliente: Pede Base1=202 → Protocolo envia 0x00C9 (201)
Resultado: ✅ Lê endereço correto (202-1 = 201, mas armazenado em 202)
```

### Exemplo Real do Log

```
👉 [UI CLICK] Clicou em DI Base0=201 (Teste_Din_bit1) → Enviando valor 1 para endereço 201

[RTU]>Tx > 12:48:40:433 - 1E 02 00 C8 00 01 3A 5B
                              ↑  ↑  ^^^^
                              │  │  └─ 0x00C8 = 200 (Base0)
                              │  └─ Function 02 (Read DI)
                              └─ Slave ID 30

[RTU]>Rx > 12:48:40:443 - 1E 02 01 01 67 9C
                              ↑  ↑  ↑  ↑
                              │  │  │  └─ Valor: 0x01 (ON)
                              │  │  └─ Byte count: 1
                              │  └─ Function 02
                              └─ Slave ID 30
```

**Análise:**
- Cliente pediu Base1=202
- Protocolo transmitiu 0x00C8 (200 em Base0)
- Servidor retornou valor armazenado em 201 (200+1)

---

## 🔄 Fluxo Completo

### Escrita (UI → Modbus → Cliente)

```
1. Usuário digita "12,34" no campo tensao_retificador (Base0=300, resolução=0.01)
   ↓
2. Sistema converte vírgula: "12,34" → "12.34"
   ↓
3. Sistema aplica resolução: 12.34 / 0.01 = 1234
   ↓
4. Sistema aplica offset: armazena em 301 (300+1)
   ↓
5. Cliente Modbus pede Base1=30301
   ↓
6. Protocolo transmite 0x012C (300 em Base0)
   ↓
7. Servidor retorna valor de 301 (300+1) = 1234
   ↓
8. Cliente recebe 1234 e aplica resolução: 1234 × 0.01 = 12.34V
```

### Leitura (Cliente → Modbus → UI)

```
1. Cliente escreve 2200 no endereço Base1=30305 (tensao_consumidor)
   ↓
2. Protocolo transmite para Base0=304
   ↓
3. Servidor armazena em 305 (304+1)
   ↓
4. Polling detecta mudança em 305
   ↓
5. Sistema aplica resolução: 2200 × 0.01 = 22.00
   ↓
6. UI atualiza campo Base0=304 com "22.0"
```

---

## 📝 Formato do CSV

```csv
Tipo,RegBase0,RegBase1,Objeto,Unidade,Resolucao,Permissao,FCs,Intervalo,ValorInicial,Descricao
IREG,300,30301,tensao_retificador,V,0.01,R,4,,,Tensao do retificador
IREG,69,30070,frequencia,Hz,0.1,R,4,,,Frequencia da rede
DISC,201,10202,Teste_Din_bit1,none,1,R,2,,,Entrada digital bit 1
COIL,208,209,Teste_Dout_pri_bit0,none,1,R/W,1/5,,OFF,Saida digital primaria bit 0
```

**Colunas importantes:**
- `RegBase0`: Endereço Base0 (usado na UI)
- `RegBase1`: Endereço Base1 (documentação)
- `Resolucao`: Fator de conversão (0.01, 0.1, 1, etc.)
- `ValorInicial`: Valor inicial (pode ser número ou ON/OFF)

---

## 🐛 Troubleshooting

### Problema: Valores com casas decimais erradas

**Causa:** Resolução incorreta no CSV

**Solução:** Verificar coluna `Resolucao` no CSV
```csv
# ERRADO
IREG,300,30301,tensao,V,1,R,4,,,Tensao

# CORRETO
IREG,300,30301,tensao,V,0.01,R,4,,,Tensao
```

### Problema: Cliente lê endereço errado

**Causa:** Offset +1 não aplicado

**Solução:** Verificar se código usa `addr + 1`:
```python
# ERRADO
self.modbus.set_value(2, addr, value)

# CORRETO
self.modbus.set_value(2, addr + 1, value)
```

### Problema: Vírgula não aceita

**Causa:** Conversão não implementada

**Solução:** Verificar se campo tem `textChanged`:
```python
entry.textChanged.connect(lambda text, e=entry: 
    e.setText(text.replace(',', '.')) if ',' in text else None)
```

---

## ✅ Checklist de Implementação

- [x] Parser lê coluna `Resolucao` do CSV
- [x] Escrita aplica resolução: `valor_modbus = int(valor_real / resolucao)`
- [x] Leitura aplica resolução: `valor_real = valor_modbus * resolucao`
- [x] Escrita aplica offset: `set_value(tipo, addr + 1, valor)`
- [x] Leitura aplica offset: `get_value(tipo, addr + 1)`
- [x] Conversão automática vírgula→ponto em tempo real
- [x] Debug logs mostram valores reais e Modbus

---

## 📚 Referências

- **Protocolo Modbus:** https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf
- **Base0 vs Base1:** Seção 4.4 do protocolo Modbus
- **pymodbus:** https://pymodbus.readthedocs.io/

---

**Versão:** 1.0.0  
**Data:** 2025-01-16  
**Autor:** Marcel Hilleshein
