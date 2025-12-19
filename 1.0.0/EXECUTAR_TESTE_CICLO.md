# 🧪 Teste de Ciclo: Iniciar/Parar 5 Vezes

## 🎯 Objetivo

Testar se a porta COM é liberada corretamente após parar o servidor, executando 5 ciclos completos de iniciar → parar → verificar.

## 🚀 Como Executar

```bash
cd "Z:\111 PUB\01 INTRANET\Marcel Hilleshein\PROJ\SimuladorBMS\1.0.0"
.venv\Scripts\activate
python test_start_stop_cycle.py
```

## 📋 O que o teste faz

Para cada um dos 5 ciclos:

1. ✅ **Verifica porta disponível** - Antes de iniciar
2. ✅ **Inicia servidor Modbus** - Na porta COM13
3. ⏱️ **Aguarda 2 segundos** - Servidor rodando
4. 🛑 **Para servidor** - Cancela tasks, fecha porta
5. ⏱️ **Aguarda 3 segundos** - Para Windows liberar
6. ✅ **Verifica porta liberada** - Tenta abrir novamente

## 📊 Resultados Possíveis

### ✅ Sucesso Total (5/5)
```
Ciclo 1: SUCESSO ✅
Ciclo 2: SUCESSO ✅
Ciclo 3: SUCESSO ✅
Ciclo 4: SUCESSO ✅
Ciclo 5: SUCESSO ✅

🎉 TODOS OS CICLOS PASSARAM!
```
**Significa:** Porta está sendo liberada corretamente

### ❌ Falha Parcial (ex: 2/5)
```
Ciclo 1: SUCESSO ✅
Ciclo 2: SUCESSO ✅
Ciclo 3: FALHA (porta não liberou)

⚠️ FALHOU NO CICLO 3
```
**Significa:** Porta não está sendo liberada consistentemente

### ❌ Falha Imediata (0/5)
```
Ciclo 1: FALHA (porta já em uso)

⚠️ FALHOU NO CICLO 1
```
**Significa:** Porta já está em uso por outro processo

## 🔍 Diagnóstico

Se o teste falhar, o script mostrará possíveis causas:

1. **Tasks asyncio não canceladas** → Aumentar tempo de espera após cancelar
2. **Tempo insuficiente** → Aumentar de 3s para 5s ou 10s
3. **Windows não libera** → Problema do SO, pode precisar reiniciar
4. **Thread não termina** → Problema no loop asyncio

## 🔧 Ajustes

Se necessário, edite o arquivo `test_start_stop_cycle.py`:

```python
# Linha 135: Tempo rodando
time.sleep(2)  # Aumentar se necessário

# Linha 143: Tempo para liberar
time.sleep(3)  # Aumentar para 5 ou 10
```

## 📝 Notas

- Certifique-se que **nenhum outro programa** está usando COM13
- Feche o **Device Manager** se estiver aberto
- Feche qualquer **terminal serial** (PuTTY, TeraTerm, etc)
- O teste demora ~30 segundos (5 ciclos × 6 segundos)

## 🎯 Próximos Passos

Baseado no resultado:

- **5/5 sucesso:** Implementar no código principal
- **Falha parcial:** Aumentar tempo de espera
- **Falha total:** Investigar se porta está travada no Windows
