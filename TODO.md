# 📋 TODO - EmuladorMODBUSRTU

## 🐛 Bugs Conhecidos

- [ ] Nenhum bug conhecido no momento

## ✨ Melhorias Planejadas

### Interface Principal (main.py)
- [ ] Adicionar botão "Parar Servidor" separado do "Iniciar Servidor"
- [ ] Implementar log de requisições Modbus em tempo real
- [ ] Adicionar gráfico de monitoramento de valores em tempo real
- [ ] Permitir exportar valores atuais para CSV
- [ ] Adicionar tema escuro/claro

### Editor CSV (csv_editor.py)
- [ ] Implementar Ctrl+Z (Desfazer) e Ctrl+Y (Refazer)
- [ ] Adicionar busca/filtro por texto (Ctrl+F)
- [ ] Implementar copiar/colar múltiplas linhas
- [ ] Adicionar validação de endereços duplicados
- [ ] Exportar para outros formatos (JSON, XML)
- [ ] Importar de outros formatos
- [ ] Adicionar coluna de comentários

### Parser CSV (csv_parser.py)
- [ ] Validar intervalos de endereços
- [ ] Detectar conflitos de endereçamento
- [ ] Suporte a fórmulas para cálculo automático de endereços

### Servidor Modbus (bms_emulator.py)
- [ ] Implementar simulação de falhas/erros
- [ ] Adicionar modo de replay de logs
- [ ] Suporte a múltiplos Slave IDs simultâneos
- [ ] Implementar Modbus TCP além do RTU
- [ ] Adicionar autenticação/segurança

## 🎯 Funcionalidades Futuras

### Alta Prioridade
- [ ] Sistema de templates de mapas de memória
- [ ] Validação automática de integridade do mapa
- [ ] Backup automático de configurações
- [ ] Histórico de alterações no CSV

### Média Prioridade
- [ ] Simulação de cenários (bateria carregando, descarregando, etc)
- [ ] Gerador automático de mapa de memória
- [ ] Integração com banco de dados
- [ ] API REST para controle remoto

### Baixa Prioridade
- [ ] Suporte a outros protocolos (CANbus, Profibus)
- [ ] Interface web
- [ ] Aplicativo mobile para monitoramento
- [ ] Geração automática de documentação

## 📝 Documentação

- [ ] Criar guia de usuário completo
- [ ] Adicionar exemplos de uso
- [ ] Documentar API interna
- [ ] Criar vídeos tutoriais
- [ ] Tradução para inglês

## 🧪 Testes

- [ ] Criar testes unitários para csv_parser.py
- [ ] Criar testes de integração para servidor Modbus
- [ ] Testes de stress/carga
- [ ] Testes de compatibilidade com diferentes mestres Modbus

## 🔧 Refatoração

- [ ] Separar lógica de negócio da interface (main.py)
- [ ] Criar classe Config para gerenciar configurações
- [ ] Implementar logging estruturado
- [ ] Adicionar type hints em todos os métodos
- [ ] Melhorar tratamento de exceções

## 📦 Distribuição

- [ ] Criar instalador Windows (.exe)
- [ ] Criar pacote Linux (.deb, .rpm)
- [ ] Publicar no PyPI
- [ ] Criar Docker container
- [ ] CI/CD com GitHub Actions

---

**Última atualização:** 2025-01-16
**Versão atual:** 1.0.0
