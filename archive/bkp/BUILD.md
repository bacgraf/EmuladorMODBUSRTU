# 🔨 Guia de Compilação - EmuladorMODBUSRTU

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Dependências do projeto** instaladas:
   ```bash
   pip install -r requirements.txt
   ```
3. **PyInstaller** (será instalado automaticamente pelo script)

## 🚀 Compilação Rápida

### Windows

Execute o script de build:
```bash
build.bat
```

O executável será criado em: `dist\EmuladorMODBUSRTU\EmuladorMODBUSRTU.exe`

## 🔧 Compilação Manual

Se preferir compilar manualmente:

```bash
# Instalar PyInstaller
pip install pyinstaller

# Limpar builds anteriores
rmdir /s /q build dist

# Compilar
pyinstaller build.spec --clean
```

## 📦 Estrutura do Executável

Após a compilação, a pasta `dist\EmuladorMODBUSRTU\` conterá:

```
EmuladorMODBUSRTU\
├── EmuladorMODBUSRTU.exe    # Executável principal
├── _internal\                # Bibliotecas e dependências
│   ├── PyQt6\
│   ├── pymodbus\
│   ├── serial\
│   └── ... (outras DLLs)
└── ... (arquivos de suporte)
```

## ⚙️ Configurações de Build

O arquivo `build.spec` está configurado para:

- ✅ **Modo onedir** (não compactado) - Abertura rápida
- ✅ **Console habilitado** - Para ver logs e debug
- ✅ **Sem UPX** - Sem compressão adicional
- ✅ **Todas as dependências incluídas**

### Modificar Configurações

Edite `build.spec` para alterar:

- **Remover console**: `console=False` (linha 42)
- **Adicionar ícone**: `icon='icone.ico'` (linha 45)
- **Modo onefile**: Alterar para `EXE(..., onefile=True, ...)`

## 📝 Notas Importantes

### Tamanho do Executável
- **Modo onedir**: ~150-200 MB (pasta completa)
- **Abertura**: Rápida (~2-3 segundos)
- **Vantagem**: Não precisa descompactar na execução

### Antivírus
Alguns antivírus podem bloquear executáveis PyInstaller. Para resolver:
1. Adicione exceção no antivírus
2. Assine digitalmente o executável (opcional)

### Distribuição
Para distribuir o software:
1. Copie toda a pasta `dist\EmuladorMODBUSRTU\`
2. Crie um instalador (opcional) usando Inno Setup ou NSIS
3. Ou compacte em ZIP para distribuição

## 🐛 Solução de Problemas

### Erro: "PyInstaller não encontrado"
```bash
pip install pyinstaller
```

### Erro: "Módulo não encontrado"
Adicione o módulo em `hiddenimports` no `build.spec`:
```python
hiddenimports=[
    'modulo_faltando',
],
```

### Executável não inicia
1. Execute via CMD para ver erros:
   ```bash
   cd dist\EmuladorMODBUSRTU
   EmuladorMODBUSRTU.exe
   ```
2. Verifique se todas as dependências estão em `requirements.txt`

### Erro de DLL faltando
Instale Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

## 📊 Comparação de Modos

| Modo | Tamanho | Abertura | Distribuição |
|------|---------|----------|--------------|
| **onedir** | ~200 MB | Rápida | Pasta completa |
| **onefile** | ~80 MB | Lenta | Arquivo único |

**Recomendado**: onedir (configuração atual)

## ✅ Checklist de Build

- [ ] Todas as dependências instaladas
- [ ] Código testado e funcionando
- [ ] `build.spec` configurado
- [ ] Build executado com sucesso
- [ ] Executável testado em máquina limpa
- [ ] Documentação atualizada

---

**Última atualização:** 2025-01-16
