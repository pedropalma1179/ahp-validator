# AHP-BOCR Validator — AhpAnpLib (Creative Decisions Foundation)

Microserviço de validação externa para o sistema AHP-BOCR Decision Support System.  
Compara os cálculos AHP do sistema com a biblioteca **AhpAnpLib**, publicada pela  
**Creative Decisions Foundation** (mesma organização do SuperDecisions e do IJAHP).

## Referência Acadêmica

> MU, E. Creative Decisions Foundation Announces the Release of AHP/ANP Python Library.  
> **International Journal of the Analytic Hierarchy Process**, v. 15, n. 2, 2023.  
> DOI: [10.13033/ijahp.v15i2.1163](https://doi.org/10.13033/ijahp.v15i2.1163)

## Arquitetura

```
┌─────────────────────────┐     ┌──────────────────────────────┐
│   Next.js (Vercel)      │────▶│  Python (Railway)            │
│                         │     │                              │
│  /api/validate-external │     │  Flask + AhpAnpLib           │
│  Envia matrizes         │◀────│  Creative Decisions Found.   │
└─────────────────────────┘     └──────────────────────────────┘
```

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET`  | `/` | Health check — verifica se AhpAnpLib está disponível |
| `POST` | `/validate` | Valida uma única matriz de comparação pareada |
| `POST` | `/validate-project` | Valida todas as matrizes de um projeto AHP-BOCR |
| `POST` | `/calculate` | Calcula eigenvector e CR usando apenas AhpAnpLib |

## Instalação Local

```bash
cd ahp-validator
pip install -r requirements.txt
python app.py
# Servidor em http://localhost:5000
```

## Deploy no Railway

### Via GitHub (redeploy automático)

1. Fazer push dos arquivos para o repositório GitHub conectado ao Railway
2. Railway detecta os commits e faz redeploy automaticamente
3. Acompanhar em [railway.app/dashboard](https://railway.app/dashboard)

### Via CLI

```bash
railway init
railway up
```

### URL atual

```
https://web-production-49489.up.railway.app
```

## Testando

### Health check

```bash
curl https://web-production-49489.up.railway.app/
```

Resposta esperada:

```json
{
  "status": "ok",
  "service": "AHP-BOCR Validator",
  "version": "2.0.0",
  "library": "AhpAnpLib (Creative Decisions Foundation)",
  "ahpanplib_available": true
}
```

### Validar matriz

```bash
curl -X POST https://web-production-49489.up.railway.app/validate \
  -H "Content-Type: application/json" \
  -d '{
    "matrix": [[1, 3, 5, 7], [0.333, 1, 2, 4], [0.2, 0.5, 1, 2], [0.143, 0.25, 0.5, 1]],
    "items": ["Benefits", "Opportunities", "Costs", "Risks"],
    "your_weights": [0.582, 0.231, 0.120, 0.066],
    "your_cr": 0.011
  }'
```

### Validar projeto completo

```bash
curl -X POST https://web-production-49489.up.railway.app/validate-project \
  -H "Content-Type: application/json" \
  -d '{
    "matrices": {
      "bocr_merits": {
        "matrix": [[1,2,3,4],[0.5,1,2,3],[0.333,0.5,1,2],[0.25,0.333,0.5,1]],
        "items": ["B","O","C","R"],
        "your_weights": [0.4673, 0.2772, 0.1601, 0.0954],
        "your_cr": 0.012
      }
    }
  }'
```

## Integração no Next.js

### 1. Copiar arquivos

```cmd
mkdir C:\AHP-BOCR\ahp-simple\app\api\validate-external
copy validate-external-route.ts C:\AHP-BOCR\ahp-simple\app\api\validate-external\route.ts
copy ExternalValidation.tsx C:\AHP-BOCR\ahp-simple\components\ExternalValidation.tsx
```

### 2. Adicionar no page.tsx (aba Robustez & Validação)

```tsx
// No topo do arquivo
import ExternalValidation from '@/components/ExternalValidation';

// Na aba "Robustez & Validação"
<ExternalValidation
  calculation={calculation}
  project={project}
/>
```

### 3. Variável de ambiente (Vercel)

```
AHP_VALIDATOR_URL=https://web-production-49489.up.railway.app
```

## O que é validado

| Componente | Método | Tolerância |
|------------|--------|------------|
| Eigenvector | Power Method com Harker fix (AhpAnpLib) | < 0.1% |
| CR | Consistency Ratio (Saaty, 1980) | < 0.1% |
| λmax | Autovalor máximo | < 0.1% |
| RI | Random Index — tabela interna AhpAnpLib | Exato |

## Citação para Dissertação

> "Os cálculos AHP do sistema foram validados contra a biblioteca AhpAnpLib
> (Creative Decisions Foundation), com diferença máxima de X.XXX% nos vetores
> de prioridade e X.XXX% nos índices de consistência, atestando a precisão
> matemática da implementação (MU, 2023; AhpAnpLib v2.3)."

## Referências

- MU, E. (2023). Creative Decisions Foundation Announces the Release of AHP/ANP Python Library. *IJAHP*, v. 15, n. 2. DOI: 10.13033/ijahp.v15i2.1163
- SAATY, T. L. (1980). *The Analytic Hierarchy Process*. McGraw-Hill, New York.
- WIJNMALEN, D. J. D. (2007). Analysis of benefits, opportunities, costs, and risks (BOCR) with the AHP-ANP. *Mathematical and Computer Modelling*, 46(7-8), 892-905.

## Dependências

| Pacote | Versão | Função |
|--------|--------|--------|
| AhpAnpLib | ≥ 2.3.17 | Cálculos AHP/ANP — Creative Decisions Foundation |
| Flask | 3.1.0 | Web framework |
| flask-cors | 5.0.1 | CORS para chamadas cross-origin |
| numpy | ≥ 1.24.0 | Computação numérica |
| gunicorn | 23.0.0 | WSGI server para produção |

## Custo

| Plataforma | Limite Gratuito | Nota |
|------------|-----------------|------|
| Railway | 500h/mês | Ideal para uso acadêmico |
| Render | 750h/mês | Alternativa |

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Microserviço não responde | Verificar deploy no Railway dashboard |
| `ahpanplib_available: false` | Verificar `requirements.txt` inclui `AhpAnpLib>=2.3.17` |
| Diferenças acima da tolerância | Verificar reciprocidade da matriz e arredondamentos |
| CORS error | Flask-CORS já está habilitado; verificar URL no `.env` |

## Licença

Uso acadêmico — Dissertação de Mestrado em Engenharia de Produção, UNESP Guaratinguetá.
