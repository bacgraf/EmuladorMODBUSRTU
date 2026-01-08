# 🧪 Teste de Liberação de Porta Serial

## 📋 Objetivo

Diagnosticar por que a porta COM não está sendo liberada corretamente após parar o servidor Modbus.

## 🚀 Como Executar

```bash
cd "Z:\111 PUB\01 INTRANET\Marcel Hilleshein\PROJ\SimuladorBMS\1.0.0"
.venv\Scripts\activate
python test_serial_close.py
```

## 🔍 O que o teste faz

### Teste 1: Serial Básico
- Abre porta COM13 com pyserial
- Fecha a porta
- Tenta reabrir
- **Objetivo:** Verificar se pyserial básico funciona

### Teste 2: Servidor Pymodbus Normal
- Inicia servidor Modbus RTU
- Para o servidor usando:
  1. `loop.stop()`
  2. `server.server_close()`
  3. `serial_port.close()`
- Tenta reabrir porta
- **Objetivo:** Verificar método atual

### Teste 3: Servidor Pymodbus com Cancelamento
- Inicia servidor Modbus RTU
- Para o servidor usando:
  1. Cancela TODAS as tasks asyncio
  2. Para o loop
  3. Fecha servidor
  4. Fecha porta
- Tenta reabrir porta
- **Objetivo:** Testar se cancelar tasks resolve

## 📊 Resultados Esperados

✅ **Sucesso:** Todos os 3 testes conseguem reabrir a porta

❌ **Falha:** Algum teste não consegue reabrir (mostra qual método não funciona)

## 🔧 Próximos Passos

Baseado nos resultados:

1. **Se Teste 1 falha:** Problema no Windows/driver
2. **Se Teste 2 falha mas Teste 3 passa:** Precisamos cancelar tasks
3. **Se todos falham:** Precisamos aumentar tempo de espera ou usar outro método

## 📝 Notas

- Certifique-se que a porta COM13 existe e não está em uso
- Se necessário, altere a variável `PORT` no script
- O teste demora ~20 segundos para completar
