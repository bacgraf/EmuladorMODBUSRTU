# 🔧 Solução: Porta COM Não Libera

## 🚨 Problema

```
PermissionError(13, 'Acesso negado', None, 5)
Task was destroyed but it is pending!
```

A porta COM não estava sendo liberada após parar o servidor, impedindo reiniciar.

## 🔍 Causa Raiz

O **pymodbus** cria **tasks asyncio** que ficam rodando em background:
- `ModbusBaseRequestHandler.handle()` - Processa requisições
- Outras tasks internas do servidor

Quando apenas paramos o loop com `loop.stop()`, essas tasks **NÃO são canceladas** e continuam tentando acessar a porta serial, mantendo o handle aberto.

## ✅ Solução Implementada

### Antes (não funcionava):
```python
def stop(self):
    # Apenas parar loop
    self.server_loop.call_soon_threadsafe(self.server_loop.stop)
    
    # Fechar servidor
    self.server.server_close()
    
    # Fechar porta
    self.serial_port.close()
```

**Problema:** Tasks continuam rodando e segurando a porta!

### Depois (funciona):
```python
def stop(self):
    # 1️⃣ CANCELAR TODAS AS TASKS PRIMEIRO
    def cancel_all_tasks():
        tasks = asyncio.all_tasks(self.server_loop)
        for task in tasks:
            task.cancel()  # ✅ Cancela cada task
        self.server_loop.stop()
    
    self.server_loop.call_soon_threadsafe(cancel_all_tasks)
    
    # 2️⃣ Aguardar tasks serem canceladas
    time.sleep(0.2)
    
    # 3️⃣ Fechar servidor
    self.server.server_close()
    
    # 4️⃣ Fechar porta
    self.serial_port.close()
```

## 🎯 Ordem Crítica

```
┌─────────────────────────────────────┐
│ 1. Cancelar TODAS as tasks asyncio  │ ← CRÍTICO!
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 2. Parar loop asyncio               │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 3. Aguardar 0.2s (tasks finalizarem)│
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 4. Fechar servidor Modbus           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 5. Fechar porta serial              │
└─────────────────────────────────────┘
```

## 🧪 Como Testar

1. **Execute o teste:**
   ```bash
   python test_serial_close.py
   ```

2. **No emulador:**
   - Inicie o servidor
   - Pare o servidor
   - Aguarde 5 segundos
   - Tente iniciar novamente
   - ✅ Deve funcionar!

## 📊 Comparação

| Método | Cancela Tasks? | Libera Porta? |
|--------|----------------|---------------|
| `loop.stop()` apenas | ❌ NÃO | ❌ NÃO |
| `task.cancel()` + `loop.stop()` | ✅ SIM | ✅ SIM |

## 🔑 Lição Aprendada

> **Ao trabalhar com asyncio, sempre cancele as tasks antes de parar o loop!**

Tasks pendentes continuam tentando executar e podem segurar recursos (como portas seriais, sockets, arquivos, etc).

## 📝 Código Chave

```python
# Pegar todas as tasks do loop
tasks = asyncio.all_tasks(self.server_loop)

# Cancelar cada uma
for task in tasks:
    task.cancel()

# Agora sim, parar o loop
self.server_loop.stop()
```

## ✅ Status

🎉 **RESOLVIDO** - Porta COM agora é liberada corretamente!
