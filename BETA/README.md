# 🔋 EmuladorMODBUSRTU v1.0.0

Emulador de Sistema de Gerenciamento de Bateria (BMS) com interface gráfica PyQt6 e protocolo Modbus RTU Serial.

> **Status:** ✅ v1.0.0 - Release Estável

## 📋 Descrição

Emulador profissional de BMS (Battery Management System) que permite:
- Interface gráfica moderna com PyQt6
- Servidor Modbus RTU Serial assíncrono
- Carregamento dinâmico de mapa de memória via CSV
- Simulação de Coils, Discrete Inputs, Input Registers e Holding Registers
- Suporte a Broadcast (Slave ID 0) e Slave ID customizável (1-247)
- Persistência de configurações

## 🚀 Instalação Rápida

```bash
cd BETA
run.bat
```

O script automaticamente:
- Verifica dependências
- Instala se necessário
- Inicia o emulador

## 📦 Requisitos

- Python 3.8+
- PyQt6 >= 6.4.0
- pymodbus >= 3.0.0
- pyserial >= 3.5

## 🎯 Uso

1. **Executar:** `run.bat`
2. **Carregar CSV:** Clique em "Selecionar..." → escolha `examples/exemplo_mapa.csv`
3. **Configurar:** Porta COM, baudrate, Slave ID
4. **Iniciar:** Clique em "Iniciar Servidor"
5. **Interagir:** Modifique valores nas abas

## 📁 Estrutura

```
BETA/
├── src/           # Código fonte
├── tests/         # Testes (10 testes)
├── docs/          # Documentação
├── examples/      # Exemplos de CSV
└── build/         # Scripts de build
```

## 🧪 Testes

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

**Resultado:** 10/10 testes passando ✅

## 🔨 Build

```bash
cd build
build.bat
```

Executável em: `build/dist/EmuladorMODBUSRTU/`

## 📝 Versionamento

**Versão Atual:** 1.0.0  
**Formato:** [Semantic Versioning](https://semver.org/)

Ver [CHANGELOG.md](CHANGELOG.md) para histórico completo.

## 📄 Documentação

- [CHANGELOG.md](CHANGELOG.md) - Histórico de mudanças
- [QUICKSTART.md](QUICKSTART.md) - Guia rápido
- [VERSIONING.md](VERSIONING.md) - Guia de versionamento

## 👨‍💻 Autor

Marcel Hilleshein

## 📧 Suporte

Abra uma issue no GitHub para dúvidas ou sugestões.

---

**v1.0.0** - Release Estável - 2025-01-16
