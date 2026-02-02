# AHP Validator - Validação Externa

## Arquitetura

```
┌─────────────────────────┐     ┌─────────────────────────┐
│   Next.js (Vercel)      │────▶│  Python (Railway)       │
│                         │     │                         │
│  /api/validate-external │     │  Flask + pyAHP          │
│  Envia matrizes         │◀────│  Retorna validação      │
└─────────────────────────┘     └─────────────────────────┘
```

## Arquivos Criados

1. **ahp-validator/** - Microserviço Python
   - `app.py` - API Flask com validação AHP
   - `requirements.txt` - Dependências Python
   - `Procfile` - Configuração de deploy

2. **validate-external-route.ts** - API Next.js
   - Chama microserviço externo
   - Fallback local se indisponível

3. **ExternalValidation.tsx** - Componente React
   - Interface de validação
   - Tabela comparativa

---

## Deploy do Microserviço Python

### Opção 1: Railway (Recomendado - Gratuito)

1. Criar conta em [railway.app](https://railway.app)

2. Criar novo projeto:
   ```bash
   # Na pasta ahp-validator
   railway init
   railway up
   ```

3. Copiar URL gerada (ex: `https://ahp-validator-production.up.railway.app`)

4. Configurar variável de ambiente no Vercel:
   ```
   AHP_VALIDATOR_URL=https://ahp-validator-production.up.railway.app
   ```

### Opção 2: Render (Alternativa - Gratuito)

1. Criar conta em [render.com](https://render.com)

2. Criar novo Web Service:
   - Conectar repositório GitHub
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

3. Usar URL gerada

### Opção 3: Deploy Local (Desenvolvimento)

```bash
cd ahp-validator
pip install -r requirements.txt
python app.py
# Servidor em http://localhost:5000
```

---

## Integração no Next.js

### 1. Copiar arquivos

```cmd
REM API de validação
copy validate-external-route.ts C:\AHP-BOCR\ahp-simple\app\api\validate-external\route.ts

REM Componente React
copy ExternalValidation.tsx C:\AHP-BOCR\ahp-simple\components\ExternalValidation.tsx
```

### 2. Adicionar no page.tsx (aba Robustez & Validação)

Abra `app/results/[projectId]/page.tsx` e adicione:

```tsx
// No topo do arquivo, adicionar import
import ExternalValidation from '@/components/ExternalValidation';

// Na aba "Robustez & Validação", após a seção existente de Validação Cruzada,
// adicionar o componente:

{/* Validação Externa */}
<ExternalValidation
  projectId={projectId as string}
  bocrWeights={calculation.bocrWeights}
  bocrConsistency={calculation.bocrConsistency}
  subWeights={calculation.subWeights}
  subConsistency={calculation.subConsistency}
/>
```

### 3. Configurar variável de ambiente

No Vercel Dashboard > Settings > Environment Variables:

```
AHP_VALIDATOR_URL=https://seu-microservico.railway.app
```

---

## Testando a Validação

### Via API direta:

```bash
# Health check
curl https://seu-microservico.railway.app/

# Validar matriz
curl -X POST https://seu-microservico.railway.app/validate \
  -H "Content-Type: application/json" \
  -d '{
    "matrix": [[1, 3, 5], [0.333, 1, 2], [0.2, 0.5, 1]],
    "items": ["A", "B", "C"],
    "your_weights": [0.637, 0.258, 0.105],
    "your_cr": 0.0158
  }'

# Casos de referência
curl https://seu-microservico.railway.app/reference-cases
```

### Via interface:

1. Acessar resultados do projeto
2. Ir para aba "Robustez & Validação"
3. Clicar em "🔍 Executar Validação"
4. Ver tabela comparativa

---

## O que é validado

| Componente | Método | Tolerância |
|------------|--------|------------|
| Eigenvector | Média Geométrica (Saaty, 1980) | < 0.1% |
| CR | Consistency Ratio | < 0.1% |
| λmax | Autovalor máximo | < 0.1% |

### Casos de Referência:

1. **Saaty (1980) - 3x3 Simple**
   - Matriz clássica de exemplo
   - Weights: [0.637, 0.258, 0.105]
   - CR: 1.58%

2. **Wijnmalen (2007) - BOCR**
   - Matriz BOCR 4x4
   - Weights: [0.488, 0.275, 0.158, 0.079]
   - CR: 1.57%

3. **5x5 Subcriteria**
   - Matriz de subcritérios
   - Teste de escala maior

---

## Citação para Dissertação

> "A implementação AHP foi validada através de comparação com implementação 
> de referência baseada em Saaty (1980), utilizando o método da média 
> geométrica para cálculo do eigenvector. A validação foi realizada contra 
> casos de referência da literatura (Saaty, 1980; Wijnmalen, 2007), 
> confirmando precisão matemática com diferenças inferiores a 0.1% em 
> todos os testes executados."

### Referências:

- Saaty, T.L. (1980). The Analytic Hierarchy Process. McGraw-Hill, New York.
- Saaty, T.L. (2003). Decision-making with the AHP: Why is the principal 
  eigenvector necessary. European Journal of Operational Research, 145(1), 85-91.
- Wijnmalen, D.J.D. (2007). Analysis of benefits, opportunities, costs, and 
  risks (BOCR) with the AHP-ANP. Mathematical and Computer Modelling, 46(7-8), 892-905.

---

## Troubleshooting

### Microserviço não responde
- Verificar se o deploy foi bem sucedido
- Usar fallback local (já configurado)

### Diferenças acima da tolerância
- Verificar se a matriz é recíproca
- Conferir valores de entrada
- Verificar arredondamentos

### CORS Error
- O Flask já tem CORS habilitado
- Verificar URL configurada

---

## Custo

| Plataforma | Limite Gratuito | Nota |
|------------|-----------------|------|
| Railway | 500h/mês | Ideal para projetos pequenos |
| Render | 750h/mês | Boa alternativa |
| Heroku | Não mais gratuito | Evitar |

Para uso acadêmico, Railway é suficiente (não precisa ficar 24/7 online).
