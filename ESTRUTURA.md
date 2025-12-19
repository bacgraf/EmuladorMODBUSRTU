# 📁 Estrutura do Projeto SimuladorBMS

## Organização de Diretórios

```
SimuladorBMS/
│
├── BETA/                           # 🚧 Versão Beta Organizada (v0.9.0-beta)
│   ├── src/                       # Código fonte principal
│   │   ├── __init__.py
│   │   ├── main.py               # Interface PyQt6
│   │   ├── csv_parser.py         # Parser de mapa de memória
│   │   └── csv_editor.py         # Editor de CSV
│   │
│   ├── tests/                     # Testes automatizados
│   │   ├── __init__.py
│   │   └── test_csv_parser.py
│   │
│   ├── docs/                      # Documentação técnica
│   │   ├── Mapa_de_memoria_BMS.csv
│   │   └── EspecificacaoTecnica.md
│   │
│   ├── examples/                  # Exemplos de uso
│   │   └── exemplo_mapa.csv
│   │
│   ├── build/                     # Scripts de compilação
│   │   ├── build.bat
│   │   ├── build.spec
│   │   └── BUILD.md
│   │
│   ├── VERSION                    # Versão atual (0.9.0-beta)
│   ├── CHANGELOG.md              # Histórico de mudanças
│   ├── VERSIONING.md             # Guia de versionamento
│   ├── README.md                 # Documentação principal
│   ├── TODO.md                   # Funcionalidades planejadas
│   ├── requirements.txt          # Dependências de produção
│   ├── requirements-dev.txt      # Dependências de desenvolvimento
│   ├── setup.py                  # Instalação do pacote
│   └── .gitignore
│
├── archive/                       # 📦 Versões Antigas (não usar)
│   ├── prototipo/                # v0.1 - Protótipo inicial
│   ├── funcional/                # v0.5 - Versão funcional
│   └── bkp/                      # v0.8 - Backup anterior
│
├── Documentação/                  # 📚 Documentação Original (referência)
│   ├── Mapa_de_memoria_BMS.csv
│   ├── Mapa_de_memoria_TPS.csv
│   ├── EspecificacaoTecnica.md
│   └── ...
│
├── .github/                       # Configurações GitHub
│   └── copilot-instructions.md
│
├── [arquivos legados na raiz]     # ⚠️ Manter por compatibilidade
│   ├── main.py                   # (usar BETA/src/main.py)
│   ├── csv_parser.py             # (usar BETA/src/csv_parser.py)
│   ├── csv_editor.py             # (usar BETA/src/csv_editor.py)
│   └── ...
│
└── ESTRUTURA.md                   # 📄 Este arquivo
```

## 🎯 Onde Trabalhar

### Para Desenvolvimento Ativo
**Use sempre a pasta `BETA/`**

```bash
cd BETA
python src/main.py
```

### Para Referência
- `Documentação/` - Especificações e mapas de memória originais
- `archive/` - Versões antigas (apenas consulta)

### Arquivos Legados (Raiz)
Mantidos por compatibilidade, mas **NÃO EDITAR**.
Todas as mudanças devem ser feitas em `BETA/`.

## 🚀 Workflow de Desenvolvimento

1. **Trabalhar em BETA/**
   ```bash
   cd BETA
   # Editar arquivos em src/
   # Adicionar testes em tests/
   ```

2. **Testar**
   ```bash
   pytest tests/
   python src/main.py
   ```

3. **Atualizar Versão**
   - Editar `VERSION`
   - Atualizar `CHANGELOG.md`
   - Atualizar `src/__init__.py`

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: nova funcionalidade"
   ```

5. **Release**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

## 📌 Próximos Passos

### Para v1.0.0 (Release Estável)
- [ ] Adicionar testes completos
- [ ] Implementar persistência de configurações
- [ ] Adicionar log de requisições Modbus
- [ ] Validar endereços duplicados no CSV
- [ ] Simplificar sistema de threading
- [ ] Revisar documentação

### Após v1.0.0
- [ ] Limpar arquivos legados da raiz
- [ ] Mover `BETA/` para raiz (renomear projeto)
- [ ] Publicar no PyPI
- [ ] Criar releases no GitHub

## 📖 Documentação

- [BETA/README.md](BETA/README.md) - Documentação principal
- [BETA/CHANGELOG.md](BETA/CHANGELOG.md) - Histórico de mudanças
- [BETA/VERSIONING.md](BETA/VERSIONING.md) - Guia de versionamento
- [BETA/TODO.md](BETA/TODO.md) - Funcionalidades planejadas

## ❓ FAQ

**P: Por que manter arquivos na raiz?**
R: Compatibilidade com scripts e configurações existentes. Serão removidos após v1.0.0.

**P: Posso deletar a pasta archive/?**
R: Sim, mas recomenda-se manter como backup histórico.

**P: Onde adiciono novas funcionalidades?**
R: Sempre em `BETA/src/`. Nunca edite arquivos da raiz.

**P: Como faço build do executável?**
R: `cd BETA/build && build.bat`
