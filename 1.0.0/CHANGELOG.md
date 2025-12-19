# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2025-01-16

### 🎉 Release Estável

Primeira versão estável do EmuladorMODBUSRTU!

### Adicionado
- Interface gráfica PyQt6 moderna e responsiva
- Servidor Modbus RTU Serial assíncrono
- Carregamento dinâmico de mapa de memória via CSV
- Editor de CSV integrado com validação
- Suporte a Coils, Discrete Inputs, Input Registers e Holding Registers
- Suporte a Broadcast (Slave ID 0) e Slave ID customizável (1-247)
- Callbacks event-driven para atualização em tempo real
- Persistência de configurações em config.json
- Tratamento robusto de erros de porta serial
- Logs detalhados no console
- Delay de 8s após parar servidor para liberar porta
- Testes automatizados (10 testes)
- Estrutura de versionamento profissional

### Funcionalidades
- Configuração completa de porta serial (COM, baudrate, paridade, stop bits)
- Monitoramento em tempo real de registradores
- Filtros por tipo de registrador no editor
- Atalhos de teclado no editor (Ctrl+S, Ctrl+D, etc)
- Modo dinâmico vs modo planilha no editor
- Validação automática de campos numéricos
- Configurações salvas automaticamente

### Testado
- 10 testes unitários passando
- run.bat validado
- Compatibilidade Windows
- pymodbus 3.x

---

## [0.9.1-beta] - 2025-01-16

### Adicionado
- Módulo config.py para persistência de configurações
- Testes completos para csv_parser (6 testes)
- Testes completos para config (4 testes)
- Configurações salvas automaticamente em config.json
- Estrutura de versionamento profissional (BETA/)

### Modificado
- main.py agora usa Config para carregar/salvar settings
- Configurações de porta serial persistem entre sessões
- Slave ID persiste entre sessões

---

## [0.9.0-beta] - 2025-01-16

### Adicionado
- Interface gráfica PyQt6 moderna
- Servidor Modbus RTU Serial assíncrono
- Carregamento dinâmico de mapa de memória via CSV
- Editor de CSV integrado com validação
- Suporte a Coils, Discrete Inputs, Input Registers e Holding Registers
- Suporte a Broadcast (Slave ID 0) e Slave ID customizável (1-247)
- Callbacks event-driven para atualização em tempo real
- Tratamento robusto de erros de porta serial
- Logs detalhados no console
- Delay de 8s após parar servidor para liberar porta

### Funcionalidades
- Configuração completa de porta serial (COM, baudrate, paridade, stop bits)
- Monitoramento em tempo real de registradores
- Filtros por tipo de registrador no editor
- Atalhos de teclado no editor (Ctrl+S, Ctrl+D, etc)
- Modo dinâmico vs modo planilha no editor
- Validação automática de campos numéricos

### Conhecido
- Threading complexo (QThread + threading.Thread + asyncio)
- Sem persistência de configurações (exceto último CSV)
- Sem testes automatizados

---

**Legenda:**
- `Adicionado` para novas funcionalidades
- `Modificado` para mudanças em funcionalidades existentes
- `Descontinuado` para funcionalidades que serão removidas
- `Removido` para funcionalidades removidas
- `Corrigido` para correção de bugs
- `Segurança` para vulnerabilidades corrigidas
