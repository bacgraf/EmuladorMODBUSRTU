# 📌 Guia de Versionamento

## Estrutura de Versão

Seguimos **Semantic Versioning 2.0.0**: `MAJOR.MINOR.PATCH[-PRERELEASE]`

### Exemplos:
- `0.9.0-beta` - Versão beta antes do lançamento 1.0.0
- `1.0.0` - Primeira versão estável
- `1.1.0` - Nova funcionalidade compatível
- `1.1.1` - Correção de bug
- `2.0.0` - Mudança incompatível (breaking change)

## Fluxo de Versionamento

### 1. Durante Desenvolvimento
```bash
# Trabalhar na branch develop ou feature
git checkout -b feature/nova-funcionalidade
# ... fazer alterações ...
git commit -m "feat: adiciona log de requisições Modbus"
```

### 2. Preparar Release
```bash
# Atualizar VERSION
echo "1.0.0" > VERSION

# Atualizar CHANGELOG.md
# Adicionar seção [1.0.0] - YYYY-MM-DD

# Atualizar __init__.py
# __version__ = "1.0.0"

# Commit de versão
git add VERSION CHANGELOG.md src/__init__.py
git commit -m "chore: bump version to 1.0.0"
```

### 3. Criar Tag
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Convenção de Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Nova funcionalidade (MINOR)
- `fix:` - Correção de bug (PATCH)
- `docs:` - Mudanças na documentação
- `style:` - Formatação de código
- `refactor:` - Refatoração sem mudança de funcionalidade
- `test:` - Adicionar ou modificar testes
- `chore:` - Tarefas de manutenção
- `BREAKING CHANGE:` - Mudança incompatível (MAJOR)

### Exemplos:
```bash
git commit -m "feat: adiciona suporte a Modbus TCP"
git commit -m "fix: corrige erro ao fechar porta serial"
git commit -m "docs: atualiza README com novos exemplos"
git commit -m "refactor: simplifica sistema de threading"
git commit -m "test: adiciona testes para csv_parser"
```

## Checklist de Release

### Beta → v1.0.0
- [ ] Todos os testes passando
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] VERSION atualizado
- [ ] Build testado (executável funciona)
- [ ] Exemplos testados
- [ ] README revisado

### Patch (1.0.0 → 1.0.1)
- [ ] Bug corrigido e testado
- [ ] CHANGELOG.md atualizado
- [ ] VERSION atualizado
- [ ] Commit e tag criados

### Minor (1.0.0 → 1.1.0)
- [ ] Nova funcionalidade testada
- [ ] Compatibilidade mantida
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] VERSION atualizado
- [ ] Exemplos atualizados (se necessário)

### Major (1.0.0 → 2.0.0)
- [ ] Breaking changes documentados
- [ ] Guia de migração criado
- [ ] Todos os testes atualizados
- [ ] CHANGELOG.md com seção "Breaking Changes"
- [ ] VERSION atualizado
- [ ] Comunicação aos usuários

## Branches

- `main` - Versão estável (releases)
- `develop` - Desenvolvimento ativo
- `feature/*` - Novas funcionalidades
- `bugfix/*` - Correções de bugs
- `hotfix/*` - Correções urgentes em produção

## Arquivos a Atualizar

Ao criar nova versão, atualizar:
1. `VERSION`
2. `CHANGELOG.md`
3. `src/__init__.py` (`__version__`)
4. `setup.py` (se necessário)
5. `README.md` (se necessário)
