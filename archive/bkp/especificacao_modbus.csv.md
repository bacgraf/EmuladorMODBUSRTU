
# Especificação Oficial do Arquivo CSV de Registradores Modbus

## 1. Objetivo
Este documento define o padrão oficial para arquivos `.csv` utilizados para carregar registradores Modbus em um Slave RTU. O formato foi projetado para ser completo, claro e compatível com aplicações industriais.

---

## 2. Estrutura Geral do CSV

Cada linha do arquivo representa **um único objeto Modbus** (coil, discrete input, input register ou holding register).

### Cabeçalho oficial:

```
Tipo,RegBase0,RegBase1,Objeto,Unidade,Resolucao,Permissao,FCs,Intervalo,ValorInicial,Descricao
```

---

## 3. Descrição dos Campos

### **Tipo**
Define o tipo Modbus:
- COIL — Bobina (bit de saída)
- DISC — Discrete Input (bit de entrada)
- HREG — Holding Register (palavra RW)
- IREG — Input Register (palavra R)

---

### **RegBase0**
Endereço em base 0.  
Exemplo: 0, 1, 2...

---

### **RegBase1**
Endereço comercial:
- COIL → 00001–09999  
- DISC → 10001–19999  
- IREG → 30001–39999  
- HREG → 40001–49999  

---

### **Objeto**
Nome simbólico do registrador.  
Exemplos:
- TensaoSaida  
- CorrenteRMS  
- Setpoint  

---

### **Unidade**
Unidade física, se aplicável:
- V, A, °C, %, none...

---

### **Resolucao**
Fator de escala.  
Exemplos:
- 0.1 → valor real = raw × 0.1  
- 1 → sem escala  
- 0.01 → centésimos  

---

### **Permissao**
Define operações permitidas:
- R  
- W  
- RW  

---

### **FCs**
Lista de Function Codes válidos para o item.  
Separados por "/", por exemplo:
- `3/16`
- `1/5`
- `4`
- `2`

---

### **Intervalo**
Faixa válida para escrita:  
Formato: `min-max`  
Exemplos:
- 0-5000  
- -400-1250  
- 0-1  

Coils e Discrete Inputs usam normalmente 0–1.

---

### **ValorInicial**
Valor carregado pelo software ao inicializar a tabela.  
Se vazio, assume 0.

---

### **Descricao**
Texto opcional explicando a função do objeto.

---

## 4. Validações Recomendadas

### **Validação Tipo × FC**
- COIL → FC 1, 5  
- DISC → FC 2  
- HREG → FC 3, 6, 16  
- IREG → FC 4  

---

### **Validação Permissão × FC**
- R → apenas FCs de leitura  
- W → apenas FCs de escrita  
- RW → ambos  

---

### **Validação de Intervalo**
Antes de aplicar escrita:
- Verificar se valor está dentro de `Intervalo`.

---

## 5. Observações Importantes

- FC17 (Report Slave ID) é global e não aparece no CSV.  
- O arquivo deve estar em UTF-8 sem BOM.  
- O software deve rejeitar linhas com inconsistências.

---

## 6. Exemplo de Linha (comentado)

```
HREG,2,40003,SetpointCorrente,A,0.01,RW,3/16,0-20000,1500,Setpoint programado pelo usuário
```

---

## 7. Conclusão

Este padrão garante:
- Consistência
- Portabilidade
- Validação robusta
- Compatibilidade com Modbus RTU industrial

---

